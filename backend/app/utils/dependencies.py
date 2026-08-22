"""
Dependency for JWT token verification
"""

from typing import Any
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from .security import SecurityManager
from sqlalchemy.orm import Session
from .database import get_db
from ..models import User, TokenBlacklist
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)  # Allow us to handle missing credentials


async def get_current_user(
    request: Request,
    credentials: Any = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token (cookie or bearer)"""
    
    token = None
    
    # Try to get token from cookie first (HttpOnly)
    token = request.cookies.get("access_token")
    
    # Fall back to Bearer token header if cookie not found
    if not token and credentials:
        token = credentials.credentials
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No access token provided",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    payload = SecurityManager.verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Check if token is blacklisted (revoked)
    jti = payload.get("jti")
    if jti:
        blacklist_entry = db.query(TokenBlacklist).filter(
            TokenBlacklist.token_jti == jti
        ).first()
        
        if blacklist_entry:
            logger.warning(f"Attempt to use revoked token: {jti[:8]}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked. Please log in again.",
                headers={"WWW-Authenticate": "Bearer"}
            )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    return user
