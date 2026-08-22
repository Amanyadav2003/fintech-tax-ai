"""
Authentication & Security Module
Handles JWT tokens, password hashing, encryption
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet, InvalidToken
import os
import uuid
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

# Password hashing - support both sha256_crypt and bcrypt for backward compatibility
# New passwords use sha256_crypt, old bcrypt hashes still work
pwd_context = CryptContext(schemes=["sha256_crypt", "bcrypt"], deprecated="auto")

# Environment variable validation
def _get_required_env(key: str, min_length: int = 32) -> str:
    """Get required environment variable with validation"""
    value = os.getenv(key)
    
    if not value:
        raise RuntimeError(
            f"CRITICAL: Environment variable '{key}' must be set. "
            f"Application cannot start without it."
        )
    
    if len(value) < min_length:
        raise RuntimeError(
            f"CRITICAL: {key} must be at least {min_length} characters. "
            f"Current length: {len(value)}"
        )
    
    return value

# JWT Configuration - SECURE: Requires environment variables, fails fast
try:
    SECRET_KEY = _get_required_env("SECRET_KEY", 32)
    ENCRYPTION_KEY = _get_required_env("ENCRYPTION_KEY", 32)
except RuntimeError as e:
    logger.critical(f"Configuration error: {e}")
    raise

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


class SecurityManager:
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token with JTI for revocation"""
        to_encode = data.copy()
        jti = str(uuid.uuid4())  # Unique token ID for revocation
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": expire,
            "jti": jti,  # Add JTI claim for revocation
            "iat": datetime.utcnow()
        })
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """Create JWT refresh token with JTI for revocation"""
        to_encode = data.copy()
        jti = str(uuid.uuid4())  # Unique token ID for revocation
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode.update({
            "exp": expire,
            "type": "refresh",
            "jti": jti,  # Add JTI claim for revocation
            "iat": datetime.utcnow()
        })
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> dict:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError as e:
            logger.debug(f"Token verification failed: {e}")
            return None
    
    @staticmethod
    def _validate_encryption_key() -> Fernet:
        """Validate and get Fernet instance"""
        try:
            # Validate key format and create Fernet instance
            key_bytes = ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY
            return Fernet(key_bytes)
        except Exception as e:
            logger.critical(f"Invalid ENCRYPTION_KEY format: {e}")
            raise ValueError(
                "CRITICAL: Invalid ENCRYPTION_KEY format. "
                "Must be a base64-encoded 32-byte key from Fernet.generate_key()"
            )
    
    @staticmethod
    def encrypt_field(data: str) -> str:
        """Encrypt sensitive field - fails fast on error, never stores plaintext"""
        if not data:
            return None
        
        try:
            # Validate key before encrypting
            fernet = SecurityManager._validate_encryption_key()
            
            # Encrypt
            encrypted = fernet.encrypt(data.encode())
            return encrypted.decode()
        
        except ValueError as e:
            logger.critical(f"CRITICAL: Encryption configuration error: {e}")
            raise  # Re-raise to prevent fallback to plaintext
        
        except Exception as e:
            logger.critical(
                f"CRITICAL: Encryption failed for sensitive data. "
                f"Operation aborted to prevent plaintext storage: {e}"
            )
            raise ValueError(
                "Unable to encrypt sensitive data - operation aborted. "
                "This is intentional - never store sensitive data unencrypted."
            )
    
    @staticmethod
    def decrypt_field(encrypted_data: str) -> str:
        """Decrypt sensitive field"""
        if not encrypted_data:
            return None
        
        try:
            fernet = SecurityManager._validate_encryption_key()
            decrypted = fernet.decrypt(encrypted_data.encode())
            return decrypted.decode()
        
        except InvalidToken as e:
            logger.error(f"Invalid encryption token (corrupted data): {e}")
            raise ValueError("Unable to decrypt - data may be corrupted")
        
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError(f"Unable to decrypt sensitive data: {e}")
