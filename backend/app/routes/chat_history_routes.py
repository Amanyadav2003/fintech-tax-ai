"""
Chat History Routes - Manage conversation history and provide retrieval/analytics
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime, timedelta

from ..models import User, ChatHistory
from ..schemas.tax_schemas import (
    ChatMessage, ChatHistoryRequest, ChatHistoryResponse, 
    ChatFeedback, ChatAnalytics
)
from ..utils.database import get_db
from ..utils.dependencies import get_current_user
from ..utils.logging_config import logger
from ..utils.middleware import limiter

router = APIRouter(prefix="/api/tax/history", tags=["chat-history"])


@router.get("/chat", response_model=ChatHistoryResponse)
@limiter.limit("20/minute")
def get_chat_history(
    request: Request,
    session_id: str = None,
    limit: int = 50,
    offset: int = 0,
    module_filter: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve chat history for user, optionally filtered by session or module"""
    
    try:
        # Base query
        query = db.query(ChatHistory).filter(ChatHistory.user_id == current_user.id)
        
        # Filter by session if provided
        if session_id:
            query = query.filter(ChatHistory.session_id == session_id)
        
        # Filter by module if provided
        if module_filter and module_filter != "all":
            query = query.filter(ChatHistory.tax_module == module_filter)
        
        # Get total count
        total_count = query.count()
        
        # Get paginated results
        messages = query.order_by(ChatHistory.created_at.asc()).offset(offset).limit(limit).all()
        
        # Convert to response models
        chat_messages = [
            ChatMessage(
                id=msg.id,
                message_type=msg.message_type,
                message_content=msg.message_content,
                operating_mode=msg.operating_mode,
                tax_module=msg.tax_module,
                response_type=msg.response_type,
                created_at=msg.created_at
            )
            for msg in messages
        ]
        
        logger.info(f"Chat history retrieved: user={current_user.id}, messages={len(chat_messages)}")
        
        return ChatHistoryResponse(
            messages=chat_messages,
            total_count=total_count
        )
    
    except Exception as e:
        logger.error(f"Error retrieving chat history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving chat history"
        )


@router.get("/sessions")
@limiter.limit("20/minute")
def get_chat_sessions(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of all chat sessions for the user"""
    
    try:
        # Get unique sessions with message counts
        sessions = db.query(
            ChatHistory.session_id,
            func.min(ChatHistory.created_at).label("first_message"),
            func.max(ChatHistory.created_at).label("last_message"),
            func.count(ChatHistory.id).label("message_count")
        ).filter(
            ChatHistory.user_id == current_user.id
        ).group_by(
            ChatHistory.session_id
        ).order_by(
            func.max(ChatHistory.created_at).desc()
        ).all()
        
        session_list = [
            {
                "session_id": session[0],
                "first_message_time": session[1],
                "last_message_time": session[2],
                "message_count": session[3]
            }
            for session in sessions
        ]
        
        logger.info(f"Chat sessions retrieved: user={current_user.id}, sessions={len(session_list)}")
        
        return {"sessions": session_list}
    
    except Exception as e:
        logger.error(f"Error retrieving chat sessions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving chat sessions"
        )


@router.delete("/chat/{message_id}")
@limiter.limit("20/minute")
def delete_chat_message(
    request: Request,
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a specific chat message (user-initiated)"""
    
    try:
        message = db.query(ChatHistory).filter(ChatHistory.id == message_id).first()
        
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        # Check ownership
        if message.user_id != current_user.id:
            logger.warning(f"Unauthorized delete attempt: user={current_user.id}, message={message_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this message"
            )
        
        db.delete(message)
        db.commit()
        
        logger.info(f"Chat message deleted: user={current_user.id}, message_id={message_id}")
        
        return {"status": "deleted", "message_id": message_id}
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting chat message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting message"
        )


@router.delete("/session/{session_id}")
@limiter.limit("10/minute")
def delete_chat_session(
    request: Request,
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an entire chat session"""
    
    try:
        # Get all messages in session
        messages = db.query(ChatHistory).filter(
            ChatHistory.session_id == session_id,
            ChatHistory.user_id == current_user.id
        ).all()
        
        if not messages:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Delete all messages in session
        for message in messages:
            db.delete(message)
        
        db.commit()
        
        logger.info(f"Chat session deleted: user={current_user.id}, session_id={session_id}, count={len(messages)}")
        
        return {"status": "deleted", "session_id": session_id, "messages_deleted": len(messages)}
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting chat session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting session"
        )


@router.post("/feedback/{message_id}")
@limiter.limit("20/minute")
def submit_chat_feedback(
    request: Request,
    message_id: int,
    feedback: ChatFeedback,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit user feedback on a chat response"""
    
    try:
        message = db.query(ChatHistory).filter(
            ChatHistory.id == message_id,
            ChatHistory.user_id == current_user.id
        ).first()
        
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        # Update message with feedback
        message.helpful = feedback.helpful
        db.commit()
        
        logger.info(f"Chat feedback submitted: user={current_user.id}, message_id={message_id}, helpful={feedback.helpful}")
        
        return {"status": "feedback_recorded", "message_id": message_id}
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error submitting feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error submitting feedback"
        )


@router.get("/analytics")
@limiter.limit("10/minute")
def get_chat_analytics(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get chat analytics and usage statistics for the user"""
    
    try:
        all_messages = db.query(ChatHistory).filter(
            ChatHistory.user_id == current_user.id
        ).all()
        
        total_conversations = len(set(msg.session_id for msg in all_messages))
        total_messages = len(all_messages)
        
        # Calculate average response length
        bot_messages = [msg for msg in all_messages if msg.message_type == "bot"]
        avg_response_length = sum(len(msg.message_content) for msg in bot_messages) / len(bot_messages) if bot_messages else 0
        
        # Get most discussed topics
        modules = {}
        modes = {}
        for msg in bot_messages:
            if msg.tax_module:
                modules[msg.tax_module] = modules.get(msg.tax_module, 0) + 1
            if msg.operating_mode:
                modes[msg.operating_mode] = modes.get(msg.operating_mode, 0) + 1
        
        most_discussed = sorted(modules.items(), key=lambda x: x[1], reverse=True)[:5]
        popular_modes = sorted(modes.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # Calculate engagement score (0-100)
        helpful_messages = len([msg for msg in all_messages if msg.helpful is True])
        engagement_score = (helpful_messages / total_messages * 100) if total_messages > 0 else 0
        
        # Get last 7 days activity
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_messages = [msg for msg in all_messages if msg.created_at >= seven_days_ago]
        
        # Group by day
        activity_by_day = {}
        for msg in recent_messages:
            day = msg.created_at.date().isoformat()
            activity_by_day[day] = activity_by_day.get(day, 0) + 1
        
        activity_list = [
            {"date": date, "message_count": count}
            for date, count in sorted(activity_by_day.items())
        ]
        
        logger.info(f"Chat analytics retrieved: user={current_user.id}")
        
        return ChatAnalytics(
            total_conversations=total_conversations,
            total_messages=total_messages,
            average_response_length=round(avg_response_length, 2),
            most_discussed_topics=[item[0] for item in most_discussed],
            popular_modules=[item[0] for item in popular_modes],
            user_engagement_score=round(engagement_score, 2),
            last_7_days_activity=activity_list
        )
    
    except Exception as e:
        logger.error(f"Error retrieving analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving analytics"
        )


@router.post("/export")
@limiter.limit("5/minute")
def export_chat_history(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export all chat history as JSON"""
    
    try:
        messages = db.query(ChatHistory).filter(
            ChatHistory.user_id == current_user.id
        ).order_by(ChatHistory.created_at.asc()).all()
        
        export_data = {
            "user_id": current_user.id,
            "export_date": datetime.utcnow().isoformat(),
            "total_messages": len(messages),
            "messages": [
                {
                    "id": msg.id,
                    "session_id": msg.session_id,
                    "message_type": msg.message_type,
                    "content": msg.message_content,
                    "mode": msg.operating_mode,
                    "module": msg.tax_module,
                    "response_type": msg.response_type,
                    "created_at": msg.created_at.isoformat(),
                    "helpful": msg.helpful
                }
                for msg in messages
            ]
        }
        
        logger.info(f"Chat history exported: user={current_user.id}, messages={len(messages)}")
        
        return export_data
    
    except Exception as e:
        logger.error(f"Error exporting chat history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error exporting history"
        )
