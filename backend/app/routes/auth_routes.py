"""
Authentication routes and JWT management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import secrets
import threading

from ..utils.security import SecurityManager
from ..utils.logging_config import logger
from ..schemas.auth_schemas import (
    UserRegister, UserLogin, UserResponse, TokenResponse,
    OTPVerification, OTPResend, RegistrationResponse
)
from ..models import User, TokenBlacklist
from ..utils.database import get_db
from ..utils.email_service import EmailDeliveryError, send_otp_email
from ..utils.middleware import limiter

router = APIRouter(prefix="/api/auth", tags=["authentication"])
resend_attempts = {}
resend_attempts_lock = threading.Lock()


def _issue_tokens(user: User) -> JSONResponse:
    access_token = SecurityManager.create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=timedelta(hours=24)
    )
    refresh_token = SecurityManager.create_refresh_token(
        data={"sub": str(user.id), "email": user.email}
    )
    response = JSONResponse(content={
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 86400,
        "message": "Login successful",
        "user": {"id": user.id, "email": user.email, "name": user.name}
    })
    response.set_cookie("access_token", access_token, httponly=True, secure=False,
                        samesite="lax", max_age=86400, path="/")
    response.set_cookie("refresh_token", refresh_token, httponly=True, secure=False,
                        samesite="lax", max_age=604800, path="/")
    return response


@router.post("/register", response_model=RegistrationResponse)
@limiter.limit("5/minute")
def register(request: Request, user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user with validation"""
    
    # Check if user exists
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.pan == user_data.pan)
    ).first()
    
    if existing_user:
        logger.warning(f"Registration attempt with existing email/PAN: {user_data.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or PAN already registered"
        )
    
    # Validate PAN format
    if len(user_data.pan) != 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid PAN format"
        )
    
    try:
        # Create new user with hashed password
        db_user = User(
            email=user_data.email,
            name=user_data.name,
            phone=user_data.phone,
            pan=user_data.pan,  # In production, encrypt this
            password_hash=SecurityManager.hash_password(user_data.password),
            age=user_data.age,
            state=user_data.state,
            is_active=True,
            email_verified=False,
            otp_code=f"{secrets.randbelow(1000000):06d}",
            otp_expires_at=datetime.utcnow() + timedelta(minutes=10)
        )
        
        db.add(db_user)
        db.flush()
        send_otp_email(user_data.email, db_user.otp_code)
        db.commit()
        db.refresh(db_user)
        
        logger.info(f"User registered successfully: {user_data.email}")
        
        return RegistrationResponse(
            email=db_user.email,
            message="Registration successful. Please verify your email with the OTP we sent you."
        )
    except EmailDeliveryError as e:
        db.rollback()
        logger.error(f"Registration email configuration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email verification is temporarily unavailable"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error during registration"
        )


@router.post("/verify-otp")
def verify_otp(payload: OTPVerification, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or user.email_verified or user.otp_code != payload.otp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OTP")
    if not user.otp_expires_at or user.otp_expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OTP")

    user.email_verified = True
    user.is_verified = True
    user.otp_code = None
    user.otp_expires_at = None
    db.commit()
    return _issue_tokens(user)


@router.post("/resend-otp")
@limiter.limit("10/minute")
def resend_otp(request: Request, payload: OTPResend, db: Session = Depends(get_db)):
    now = datetime.utcnow()
    with resend_attempts_lock:
        last_attempt = resend_attempts.get(payload.email)
        if last_attempt and now - last_attempt < timedelta(seconds=60):
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                                detail="Please wait 60 seconds before requesting another OTP")
        resend_attempts[payload.email] = now

    user = db.query(User).filter(User.email == payload.email).first()
    if not user or user.email_verified:
        return {"message": "If the account requires verification, a new OTP has been sent."}

    user.otp_code = f"{secrets.randbelow(1000000):06d}"
    user.otp_expires_at = now + timedelta(minutes=10)
    db.commit()
    try:
        send_otp_email(user.email, user.otp_code)
    except Exception:
        db.rollback()
        logger.error("OTP email delivery failed for %s", user.email)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="Unable to send verification email")
    return {"message": "A new verification OTP has been sent."}


@router.post("/login")
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Login and set secure HttpOnly cookies"""
    
    # Find user
    user = db.query(User).filter(User.email == credentials.email).first()
    
    if not user or not SecurityManager.verify_password(credentials.password, user.password_hash):
        logger.warning(f"Failed login attempt: {credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if not user.is_active:
        logger.warning(f"Login attempt by inactive user: {credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )

    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before logging in"
        )
    
    logger.info(f"User logged in successfully: {user.id}")
    return _issue_tokens(user)


@router.post("/refresh")
def refresh_token(request: Request, db: Session = Depends(get_db)):
    """Get new access token using refresh token cookie"""
    
    # Get refresh token from cookie
    refresh_token_value = request.cookies.get("refresh_token")
    
    if not refresh_token_value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found"
        )
    
    # Verify refresh token
    payload = SecurityManager.verify_token(refresh_token_value)
    
    if not payload or payload.get("type") != "refresh":
        logger.warning("Invalid refresh token attempt")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Check if token is blacklisted
    jti = payload.get("jti")
    if jti:
        blacklist_entry = db.query(TokenBlacklist).filter(
            TokenBlacklist.token_jti == jti
        ).first()
        if blacklist_entry:
            logger.warning(f"Attempt to use revoked refresh token: {jti[:8]}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")
    
    user_id = payload.get("sub")
    email = payload.get("email")
    
    # Create new access token
    new_access_token = SecurityManager.create_access_token(
        data={"sub": user_id, "email": email},
        expires_delta=timedelta(hours=24)  # 24 hours
    )
    
    logger.info(f"Token refreshed for user: {user_id}")
    
    # Create response with new access token cookie
    response = JSONResponse(
        content={"message": "Token refreshed successfully"}
    )
    
    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=86400,  # 24 hours
        path="/"
    )
    
    return response


@router.get("/verify")
def verify_token(request: Request):
    """Verify if token is valid (cookie-based)"""
    
    token = request.cookies.get("access_token")
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No access token found"
        )
    
    payload = SecurityManager.verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    return {
        "valid": True,
        "user_id": payload.get("sub"),
        "email": payload.get("email")
    }


@router.post("/logout")
def logout(
    request: Request,
    db: Session = Depends(get_db)
):
    """Logout user by revoking tokens"""
    
    try:
        # Get access token from cookie
        access_token = request.cookies.get("access_token")
        refresh_token = request.cookies.get("refresh_token")
        
        # Blacklist both tokens
        tokens_to_revoke = []
        if access_token:
            payload = SecurityManager.verify_token(access_token)
            if payload:
                tokens_to_revoke.append(payload)
        
        if refresh_token:
            payload = SecurityManager.verify_token(refresh_token)
            if payload:
                tokens_to_revoke.append(payload)
        
        # Add to blacklist
        for payload in tokens_to_revoke:
            jti = payload.get("jti")
            if jti:
                exp = payload.get("exp")
                expires_at = datetime.fromtimestamp(exp) if exp else datetime.utcnow() + timedelta(days=7)
                
                # Check if already blacklisted
                existing = db.query(TokenBlacklist).filter(
                    TokenBlacklist.token_jti == jti
                ).first()
                
                if not existing:
                    blacklist_entry = TokenBlacklist(
                        token_jti=jti,
                        user_id=payload.get("sub"),
                        expires_at=expires_at
                    )
                    db.add(blacklist_entry)
        
        db.commit()
        
        logger.info("User logged out successfully")
        
        # Create response with cleared cookies
        response = JSONResponse(
            content={"message": "Logged out successfully"}
        )
        
        # Clear cookies
        response.delete_cookie("access_token", path="/")
        response.delete_cookie("refresh_token", path="/")
        
        return response
    
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )
