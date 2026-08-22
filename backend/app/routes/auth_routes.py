"""
Authentication routes and JWT management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import secrets
import threading
from pathlib import Path
from uuid import uuid4

from ..utils.security import SecurityManager
from ..utils.logging_config import logger
from ..schemas.auth_schemas import (
    UserRegister, UserLogin, UserResponse, TokenResponse,
    OTPVerification, OTPResend, RegistrationResponse, LoginOTPVerification,
    NotificationPreferences
)
from ..models import User, TokenBlacklist
from ..utils.database import get_db
from ..utils.dependencies import get_current_user
from ..utils.email_service import EmailDeliveryError, send_otp_email
from ..utils.middleware import limiter

router = APIRouter(prefix="/api/auth", tags=["authentication"])
UPLOADS_DIR = Path("/app/uploads")
MAX_PROFILE_PHOTO_BYTES = 2 * 1024 * 1024
resend_attempts = {}
pending_registrations = {}
resend_attempts_lock = threading.Lock()


def _normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def _cleanup_expired_pending_registrations() -> None:
    now = datetime.utcnow()
    expired = [email for email, data in pending_registrations.items() if data.get("expires_at") and data["expires_at"] < now]
    for email in expired:
        pending_registrations.pop(email, None)


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


@router.post("/send-registration-otp")
@limiter.limit("60/minute")
def send_registration_otp(request: Request, payload: OTPResend, db: Session = Depends(get_db)):
    """Send an email-only OTP for registration before collecting the rest of the form."""
    email = _normalize_email(payload.email)
    _cleanup_expired_pending_registrations()

    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user and existing_user.email_verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    with resend_attempts_lock:
        last_attempt = resend_attempts.get(email)
        now = datetime.utcnow()
        if last_attempt and now - last_attempt < timedelta(seconds=60):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Please wait 60 seconds before requesting another OTP"
            )
        resend_attempts[email] = now

    otp = f"{secrets.randbelow(1000000):06d}"
    pending_registrations[email] = {
        "otp": otp,
        "expires_at": datetime.utcnow() + timedelta(minutes=10),
        "verified": False,
    }

    try:
        send_otp_email(email, otp)
    except EmailDeliveryError as exc:
        pending_registrations.pop(email, None)
        logger.error("Registration OTP email delivery failed for %s", email)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to send registration verification email"
        ) from exc

    return {"message": "Registration OTP sent to your email."}


@router.post("/verify-registration-otp")
def verify_registration_otp(payload: OTPVerification, db: Session = Depends(get_db)):
    """Verify the temporary registration OTP without creating a stale user record."""
    email = _normalize_email(payload.email)
    _cleanup_expired_pending_registrations()
    pending = pending_registrations.get(email)

    if not pending:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect OTP")

    if pending["expires_at"] < datetime.utcnow():
        pending_registrations.pop(email, None)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP expired")

    if pending["otp"] != payload.otp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect OTP")

    pending["verified"] = True
    pending["expires_at"] = datetime.utcnow() + timedelta(minutes=30)
    return {"verified": True, "message": "Email verified successfully"}


@router.post("/register", response_model=RegistrationResponse)
@limiter.limit("60/minute")
def register(request: Request, user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user only after the email has been verified via the dedicated OTP flow."""
    normalized_email = _normalize_email(user_data.email)
    _cleanup_expired_pending_registrations()
    pending = pending_registrations.get(normalized_email)
    if not pending or not pending.get("verified") or pending["expires_at"] < datetime.utcnow():
        pending_registrations.pop(normalized_email, None)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please verify your email before completing registration"
        )

    existing_user = db.query(User).filter((User.email == normalized_email) | (User.pan == user_data.pan.upper())).first()
    if existing_user:
        logger.warning(f"Registration attempt with existing email/PAN: {normalized_email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or PAN already registered"
        )

    pan_value = user_data.pan.upper()
    if len(pan_value) != 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid PAN format"
        )

    try:
        db_user = User(
            email=normalized_email,
            name=user_data.name,
            phone=user_data.phone,
            pan=pan_value,
            password_hash=SecurityManager.hash_password(user_data.password),
            age=user_data.age,
            state=user_data.state or "Maharashtra",
            is_active=True,
            is_verified=True,
            email_verified=True,
            otp_code=None,
            otp_expires_at=None,
            employment_type=user_data.employment_type or "Salaried",
            pan_aadhaar_linked=bool(user_data.pan_aadhaar_linked),
            financial_year=user_data.financial_year or "FY 2024-25 (AY 2025-26)",
            employer_name=user_data.employer_name,
            email_reminders_enabled=bool(user_data.email_reminders_enabled)
        )

        db.add(db_user)
        db.flush()
        pending_registrations.pop(normalized_email, None)
        db.commit()
        db.refresh(db_user)

        logger.info(f"User registered successfully: {normalized_email}")
        return RegistrationResponse(
            email=db_user.email,
            message="Registration successful."
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error during registration"
        )


@router.post("/registration/profile-photo")
def upload_registration_profile_photo(email: str, photo: UploadFile = File(...), db: Session = Depends(get_db)):
    """Store an optional image for an existing, not-yet-verified registration."""
    if not photo.content_type or not photo.content_type.startswith("image/"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Profile photo must be an image")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registration not found")

    contents = photo.file.read(MAX_PROFILE_PHOTO_BYTES + 1)
    if len(contents) > MAX_PROFILE_PHOTO_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Profile photo must be 2MB or smaller")

    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    extension = Path(photo.filename or "photo").suffix.lower()
    if extension not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        extension = ".bin"
    filename = f"profile_{uuid4().hex}{extension}"
    destination = UPLOADS_DIR / filename
    destination.write_bytes(contents)
    user.profile_photo_url = f"/uploads/{filename}"
    db.commit()
    return {"message": "Profile photo uploaded", "profile_photo_url": user.profile_photo_url}


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


@router.post("/login/verify-otp")
def verify_login_otp(payload: LoginOTPVerification, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not user.email_verified or user.otp_code != payload.otp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OTP")
    if not user.otp_expires_at or user.otp_expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OTP")
    user.otp_code = None
    user.otp_expires_at = None
    db.commit()
    return _issue_tokens(user)


@router.post("/login")
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Login and set secure HttpOnly cookies."""
    login_email = (credentials.login_email or '').strip().lower()
    if not login_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required"
        )

    user = db.query(User).filter(User.email == login_email).first()

    if not user or not SecurityManager.verify_password(credentials.password, user.password_hash):
        logger.warning(f"Failed login attempt: {login_email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not user.is_active:
        logger.warning(f"Login attempt by inactive user: {login_email}")
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


@router.get("/me")
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Return the authenticated user profile for the current access token."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "phone": current_user.phone,
        "pan": current_user.pan,
        "age": current_user.age,
        "state": current_user.state,
        "employment_type": current_user.employment_type,
        "pan_aadhaar_linked": current_user.pan_aadhaar_linked,
        "financial_year": current_user.financial_year,
        "employer_name": current_user.employer_name,
        "email_reminders_enabled": current_user.email_reminders_enabled,
        "profile_photo_url": current_user.profile_photo_url,
        "created_at": current_user.created_at,
    }


@router.patch("/notification-preferences")
def update_notification_preferences(payload: NotificationPreferences, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.email_reminders_enabled = payload.email_reminders_enabled
    db.commit()
    return {"email_reminders_enabled": current_user.email_reminders_enabled}


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
        content={
            "message": "Token refreshed successfully",
            "access_token": new_access_token,
            "refresh_token": refresh_token_value,
            "token_type": "bearer",
            "expires_in": 86400,
        }
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
