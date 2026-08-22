# Implementation Guide: Critical Security Fixes

## Overview
This guide provides step-by-step instructions to fix all critical security issues in the TaxMate AI application.

---

## Fix 1: Secure Secret Management

### Step 1.1: Update security.py
**File**: `backend/app/utils/security.py`

Replace lines 16-18 and 20 with:

```python
import os
from pathlib import Path

def _get_required_env(key: str, min_length: int = 32) -> str:
    """Get required environment variable with validation"""
    value = os.getenv(key)
    
    if not value:
        raise ValueError(
            f"CRITICAL: Environment variable '{key}' must be set. "
            f"Generate a secure value and add to .env file"
        )
    
    if len(value) < min_length:
        raise ValueError(
            f"CRITICAL: {key} must be at least {min_length} characters. "
            f"Current length: {len(value)}"
        )
    
    return value

# SECURE: Requires environment variables, fails fast
try:
    SECRET_KEY = _get_required_env("SECRET_KEY", 32)
    ENCRYPTION_KEY = _get_required_env("ENCRYPTION_KEY", 32)
except ValueError as e:
    raise RuntimeError(f"Configuration error: {e}")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
```

### Step 1.2: Generate secure keys
```bash
# Run these commands in terminal
cd c:\fintech-tax-ai

# Generate SECRET_KEY
python -c "import secrets; key = secrets.token_urlsafe(32); print(f'SECRET_KEY={key}')"

# Generate ENCRYPTION_KEY
python -c "from cryptography.fernet import Fernet; key = Fernet.generate_key().decode(); print(f'ENCRYPTION_KEY={key}')"

# Copy the output - you'll need these values
```

### Step 1.3: Create .env file
**File**: `backend/.env`

```bash
# Database Configuration
DATABASE_URL=postgresql://postgres:your_secure_password@db:5432/taxmate_ai
DB_USER=postgres
DB_PASSWORD=your_secure_password
DB_NAME=taxmate_ai

# Security Keys (from Step 1.2)
SECRET_KEY=<paste-generated-key-here>
ENCRYPTION_KEY=<paste-generated-key-here>

# Frontend Configuration
REACT_APP_API_URL=http://localhost:5000/api

# CORS Configuration
CORS_ORIGINS=http://localhost:3000

# Environment
ENVIRONMENT=development
APP_VERSION=1.0.0

# Optional: Sentry for error tracking
SENTRY_DSN=

# Rate Limiting
RATE_LIMIT_ENABLED=true
```

### Step 1.4: Add .env to .gitignore
**File**: `.gitignore` (create if doesn't exist)

```
.env
.env.local
.env.*.local
*.pyc
__pycache__/
.pytest_cache/
.venv/
venv/
node_modules/
build/
dist/
*.egg-info/
logs/
.DS_Store
```

---

## Fix 2: Secure Encryption Implementation

### Step 2.1: Update security.py encryption methods
**File**: `backend/app/utils/security.py`

Replace the `encrypt_field` and `decrypt_field` methods:

```python
from cryptography.fernet import Fernet, InvalidToken
import logging

logger = logging.getLogger(__name__)

class SecurityManager:
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
        """Encrypt sensitive field - fails fast on error"""
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
```

---

## Fix 3: Token Revocation (Logout Functionality)

### Step 3.1: Add TokenBlacklist model
**File**: `backend/app/models/__init__.py` (add to existing file)

```python
class TokenBlacklist(Base):
    """Stores revoked tokens to prevent reuse"""
    __tablename__ = "token_blacklist"
    
    id = Column(Integer, primary_key=True, index=True)
    token_jti = Column(String, unique=True, index=True)  # JWT ID claim
    user_id = Column(Integer, index=True)
    blacklisted_at = Column(DateTime, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime)  # When to delete this entry
    
    def __repr__(self):
        return f"<TokenBlacklist(user_id={self.user_id}, jti={self.token_jti[:8]})>"
```

### Step 3.2: Update token creation with JTI
**File**: `backend/app/utils/security.py`

Replace token creation methods:

```python
import uuid
from datetime import datetime, timedelta

class SecurityManager:
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token with JTI for revocation"""
        to_encode = data.copy()
        jti = str(uuid.uuid4())  # Unique token ID
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": expire,
            "jti": jti,  # Add JTI claim
            "iat": datetime.utcnow()
        })
        
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """Create JWT refresh token with JTI for revocation"""
        to_encode = data.copy()
        jti = str(uuid.uuid4())  # Unique token ID
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode.update({
            "exp": expire,
            "type": "refresh",
            "jti": jti,  # Add JTI claim
            "iat": datetime.utcnow()
        })
        
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
```

### Step 3.3: Add logout endpoint
**File**: `backend/app/routes/auth_routes.py` (add to existing file)

```python
@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    token: str = Depends(security),
    db: Session = Depends(get_db)
):
    """Logout by blacklisting tokens"""
    
    try:
        # Get token payload
        payload = SecurityManager.verify_token(token.credentials)
        jti = payload.get("jti")
        
        if not jti:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token format invalid"
            )
        
        # Get token expiration
        exp = payload.get("exp")
        expires_at = datetime.fromtimestamp(exp) if exp else datetime.utcnow() + timedelta(days=7)
        
        # Add to blacklist
        blacklist_entry = TokenBlacklist(
            token_jti=jti,
            user_id=current_user.id,
            expires_at=expires_at
        )
        
        db.add(blacklist_entry)
        db.commit()
        
        logger.info(f"User logged out: {current_user.email}")
        
        return {
            "message": "Logged out successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )
```

### Step 3.4: Add token revocation check
**File**: `backend/app/utils/dependencies.py` (modify existing)

```python
from sqlalchemy.orm import Session
from app.models import TokenBlacklist, User
from app.utils.database import get_db
from datetime import datetime

async def get_current_user(
    credentials: Any = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token"""
    
    token = credentials.credentials
    payload = SecurityManager.verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Check if token is blacklisted
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
```

---

## Fix 4: HttpOnly Cookie-Based Authentication

### Step 4.1: Update login endpoint
**File**: `backend/app/routes/auth_routes.py`

Replace login endpoint:

```python
from fastapi.responses import JSONResponse

@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """Login and set secure HttpOnly cookies"""
    
    # Find and verify user
    user = db.query(User).filter(User.email == credentials.email).first()
    
    if not user or not SecurityManager.verify_password(credentials.password, user.password_hash):
        logger.warning(f"Failed login attempt: {LogSanitizer.sanitize_email(credentials.email)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if not user.is_active:
        logger.warning(f"Login attempt by inactive user: {LogSanitizer.sanitize_email(credentials.email)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    # Create tokens
    access_token = SecurityManager.create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=timedelta(hours=1)  # Shorter access token
    )
    
    refresh_token = SecurityManager.create_refresh_token(
        data={"sub": str(user.id), "email": user.email}
    )
    
    logger.info(f"User logged in successfully: {user.id}")
    
    # Create response with HttpOnly cookies
    response = JSONResponse(
        content={
            "message": "Login successful",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name
            }
        }
    )
    
    # Set access token cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,          # ← Can't be read by JavaScript
        secure=True,            # ← HTTPS only in production
        samesite="strict",      # ← CSRF protection
        max_age=3600,           # ← 1 hour
        path="/"
    )
    
    # Set refresh token cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=604800,         # ← 7 days
        path="/"
    )
    
    return response
```

### Step 4.2: Update token refresh endpoint
**File**: `backend/app/routes/auth_routes.py`

```python
@router.post("/refresh")
@limiter.limit("30/minute")
async def refresh_token(
    request: Request,
    db: Session = Depends(get_db)
):
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
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    user_id = payload.get("sub")
    email = payload.get("email")
    
    # Create new access token
    new_access_token = SecurityManager.create_access_token(
        data={"sub": user_id, "email": email},
        expires_delta=timedelta(hours=1)
    )
    
    logger.info(f"Token refreshed for user: {user_id}")
    
    # Return response with new access token cookie
    response = JSONResponse(content={"message": "Token refreshed"})
    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=3600,
        path="/"
    )
    
    return response
```

### Step 4.3: Update token dependency
**File**: `backend/app/utils/dependencies.py`

```python
from fastapi import Request

async def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from HttpOnly cookie"""
    
    # Get token from cookie
    token = request.cookies.get("access_token")
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    payload = SecurityManager.verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    # Check if token is blacklisted
    jti = payload.get("jti")
    if jti:
        blacklist_entry = db.query(TokenBlacklist).filter(
            TokenBlacklist.token_jti == jti
        ).first()
        if blacklist_entry:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    return user
```

---

## Fix 5: Update Frontend to Use Cookies

### Step 5.1: Update api.js service
**File**: `frontend/src/services/api.js`

Replace entire file:

```javascript
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,  // ← Send cookies automatically
});

// Error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired - clear and redirect to login
      localStorage.clear();  // Clear any old data
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authService = {
  register: (userData) => api.post('/auth/register', userData),
  login: (credentials) => api.post('/auth/login', credentials),
  logout: () => api.post('/auth/logout'),
};

export const taxFilingService = {
  createFiling: (filingData) => api.post('/tax/filings', filingData),
  analyzeFiling: (filingId) => api.post(`/tax/analyze/${filingId}`),
  getResults: (filingId) => api.get(`/tax/results/${filingId}`),
  getDashboard: () => api.get('/tax/dashboard'),
};

export default api;
```

### Step 5.2: Update Auth.js component
**File**: `frontend/src/components/Auth.js`

```javascript
const handleSubmit = async (e) => {
  e.preventDefault();
  
  if (!validateForm()) return;
  
  setLoading(true);
  setError('');
  setSuccess('');

  try {
    if (isLogin) {
      // Login
      const response = await authService.login({
        email: formData.email,
        password: formData.password
      });
      
      // Cookies are set automatically by browser
      setSuccess('Login successful!');
      onUserCreated(formData.email);
      
    } else {
      // Register
      const response = await authService.register({
        email: formData.email,
        password: formData.password,
        name: formData.name,
        phone: formData.phone,
        pan: formData.pan,
        age: parseInt(formData.age),
        state: formData.state,
      });
      
      setSuccess('Registration successful! Please log in.');
      setIsLogin(true);
      // Reset form
      setFormData({...});
    }
  } catch (err) {
    setError(err.response?.data?.detail || err.message);
  } finally {
    setLoading(false);
  }
};
```

---

## Fix 6: Update CORS Configuration

### Step 6.1: Update main.py
**File**: `backend/app/main.py`

```python
from fastapi.middleware.cors import CORSMiddleware
import os

# Get CORS origins from environment
CORS_ORIGINS_STR = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000"  # Default for development only
)

CORS_ORIGINS = [origin.strip() for origin in CORS_ORIGINS_STR.split(",")]

# Validation
if CORS_ORIGINS == ["http://localhost:3000"] and os.getenv("ENVIRONMENT") == "production":
    raise ValueError(
        "CRITICAL: CORS_ORIGINS must be configured for production. "
        "Set CORS_ORIGINS environment variable with your domain."
    )

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,  # Allow credentials (cookies)
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # No OPTIONS needed explicitly
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-CSRF-Token",  # For CSRF protection
    ],
    expose_headers=["X-Total-Count"],  # Expose custom headers if needed
    max_age=600,  # Preflight cache 10 minutes
)
```

---

## Fix 7: Add Rate Limiting to Auth Endpoints

### Step 7.1: Update auth_routes.py
**File**: `backend/app/routes/auth_routes.py`

```python
from app.utils.middleware import limiter
from fastapi import Request

@router.post("/register", response_model=UserResponse)
@limiter.limit("5/minute")  # ← Add rate limiting
def register(
    request: Request,  # ← Add request parameter
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    # ... existing code ...

@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")  # ← Add rate limiting
def login(
    request: Request,  # ← Add request parameter
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    # ... existing code ...

@router.post("/forgot-password")
@limiter.limit("3/minute")  # ← Even stricter for password reset
def forgot_password(
    request: Request,
    email: str,
    db: Session = Depends(get_db)
):
    # Implementation for password reset...
```

---

## Fix 8: Secure Docker Configuration

### Step 8.1: Update backend Dockerfile
**File**: `backend/Dockerfile`

```dockerfile
FROM python:3.11-slim

# Create non-root user
RUN groupadd -r appuser && \
    useradd -r -g appuser appuser

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    curl && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=appuser:appuser . .

# Create logs directory with correct permissions
RUN mkdir -p logs && \
    chown appuser:appuser logs

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Step 8.2: Update docker-compose.yml
**File**: `docker-compose.yml`

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    container_name: taxmate_db
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ${DB_NAME}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - taxmate_network

  backend:
    build: ./backend
    container_name: taxmate_backend
    ports:
    - "5000:5000"
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}
      SECRET_KEY: ${SECRET_KEY}
      ENCRYPTION_KEY: ${ENCRYPTION_KEY}
      CORS_ORIGINS: ${CORS_ORIGINS}
      ENVIRONMENT: ${ENVIRONMENT}
      SENTRY_DSN: ${SENTRY_DSN}
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - ./backend/logs:/app/logs
    command: uvicorn app.main:app --host 0.0.0.0 --port 5000
    networks:
      - taxmate_network
    restart: unless-stopped

  frontend:
    build: ./frontend
    container_name: taxmate_frontend
    ports:
      - "3000:3000"
    environment:
      REACT_APP_API_URL: ${REACT_APP_API_URL}
    depends_on:
      - backend
    networks:
      - taxmate_network
    restart: unless-stopped

volumes:
  postgres_data:
    driver: local

networks:
  taxmate_network:
    driver: bridge
```

---

## Fix 9: Database Encryption

### Step 9.1: Add EncryptedString type to models
**File**: `backend/app/models/__init__.py`

Add at the top of file:

```python
from sqlalchemy.types import TypeDecorator, String as SQLString
from app.utils.security import SecurityManager

class EncryptedString(TypeDecorator):
    """Custom SQLAlchemy type that automatically encrypts/decrypts"""
    
    impl = SQLString
    cache_ok = True
    
    def process_bind_param(self, value, dialect):
        """Encrypt value before storing in database"""
        if value is None:
            return value
        
        return SecurityManager.encrypt_field(value)
    
    def process_result_value(self, value, dialect):
        """Decrypt value when retrieving from database"""
        if value is None:
            return value
        
        return SecurityManager.decrypt_field(value)
```

### Step 9.2: Update User model
Replace in User class:

```python
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    phone = Column(EncryptedString)  # ← Now encrypted
    pan = Column(EncryptedString, unique=True, index=False)  # ← Now encrypted, remove index
    password_hash = Column(String)
    age = Column(Integer)
    state = Column(String)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

---

## Fix 10: Run Database Migrations

### Step 10.1: Create migration
```bash
cd c:\fintech-tax-ai\backend

# Initialize Alembic if not already done
alembic init alembic

# Create migration for TokenBlacklist table
alembic revision --autogenerate -m "Add TokenBlacklist table"

# Apply migration
alembic upgrade head
```

---

## Verification Checklist

After implementing all fixes:

- [ ] No hardcoded secrets in code
- [ ] ENCRYPTION_KEY required via environment
- [ ] Tokens in HttpOnly cookies
- [ ] Logout endpoint working
- [ ] Rate limiting on auth endpoints
- [ ] Docker runs as non-root
- [ ] CORS restricted to allowed origins
- [ ] PAN/phone encrypted in database
- [ ] Tests pass
- [ ] Security audit clean

## Testing the Fixes

```bash
cd c:\fintech-tax-ai

# 1. Start services
docker-compose up

# 2. Test login with new HttpOnly cookies
curl -c cookies.txt -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"TestPass123!"}'

# 3. Verify cookies set
cat cookies.txt

# 4. Test logout
curl -b cookies.txt -X POST http://localhost:5000/api/auth/logout

# 5. Run tests
pytest backend/tests/ -v

# 6. Security scan
bandit -r backend/app/
```

