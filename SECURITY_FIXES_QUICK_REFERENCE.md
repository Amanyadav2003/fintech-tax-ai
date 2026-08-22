# Quick Reference: Critical Issues & Fixes

## 🚨 CRITICAL FIXES REQUIRED (Do Before Production)

### Issue #1: Hardcoded Secrets
**File**: `backend/app/utils/security.py:16-18`
```python
# BEFORE (VULNERABLE)
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production-32-char-minimum")

# AFTER (FIXED)
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("CRITICAL: SECRET_KEY environment variable must be set")
```

### Issue #2: Encryption Fallback to Plaintext
**File**: `backend/app/utils/security.py:65`
```python
# BEFORE (VULNERABLE)
except Exception as e:
    print(f"Encryption error: {e}")
    return data  # ← Returns plaintext!

# AFTER (FIXED)
except Exception as e:
    logger.error(f"Encryption failed: {e}")
    raise ValueError("Critical encryption failure - operation aborted")
```

### Issue #3: Token Revocation Missing
**File**: `backend/app/routes/auth_routes.py:104-130`
```python
# ADD: Logout endpoint
@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Logout by revoking tokens"""
    token_entry = TokenBlacklist(
        token_jti=request.state.token_jti,
        user_id=current_user.id,
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    db.add(token_entry)
    db.commit()
    return {"message": "Logged out successfully"}
```

### Issue #6: Tokens Stored in localStorage (XSS Vulnerable)
**File**: `frontend/src/services/api.js` & `frontend/src/components/Auth.js`
```javascript
// BEFORE (VULNERABLE)
localStorage.setItem('access_token', data.access_token);

// AFTER (FIXED)
// Backend sets HttpOnly cookies:
response.set_cookie(
    key="access_token",
    value=access_token,
    httponly=True,      # Cannot be read by JS
    secure=True,        # HTTPS only
    samesite="strict"   # CSRF protection
)

// Frontend doesn't need to store tokens
api.interceptors.request.use(config => {
    config.withCredentials = true;  // Cookies sent automatically
    return config;
});
```

### Issue #7: CORS Too Permissive
**File**: `backend/app/main.py:52`
```python
# BEFORE (VULNERABLE)
allow_headers=["*"],  # TOO PERMISSIVE

# AFTER (FIXED)
allow_headers=["Content-Type", "Authorization"],
max_age=600  # Preflight cache 10 minutes
```

### Issue #12: Secrets in docker-compose.yml
**File**: `docker-compose.yml`
```yaml
# BEFORE (VULNERABLE)
environment:
  POSTGRES_PASSWORD: password

# AFTER (FIXED)
environment:
  POSTGRES_PASSWORD: ${DB_PASSWORD}  # From .env file

# Add to .gitignore:
.env
.env.local
```

### Issue #18: PAN Stored Unencrypted
**File**: `backend/app/models/__init__.py:10`
```python
# BEFORE (VULNERABLE)
pan = Column(String, unique=True, index=True)  # Plaintext

# AFTER (FIXED)
from sqlalchemy.types import TypeDecorator

class EncryptedString(TypeDecorator):
    impl = String
    cache_ok = True
    
    def process_bind_param(self, value, dialect):
        if value: return SecurityManager.encrypt_field(value)
    
    def process_result_value(self, value, dialect):
        if value: return SecurityManager.decrypt_field(value)

class User(Base):
    pan = Column(EncryptedString, unique=True, index=False)
```

---

## 🔧 Quick Fixes (Copy-Paste Ready)

### 1. Add to docker-compose.yml environment
```yaml
backend:
  environment:
    - SECRET_KEY=${SECRET_KEY}
    - ENCRYPTION_KEY=${ENCRYPTION_KEY}
    - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}
    - CORS_ORIGINS=${CORS_ORIGINS}
    - SENTRY_DSN=${SENTRY_DSN}
```

### 2. Create .env.example
```bash
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/taxmate_ai

# Security - GENERATE NEW VALUES!
SECRET_KEY=change-me-min-32-chars
ENCRYPTION_KEY=change-me-base64-fernet-key

# Frontend
REACT_APP_API_URL=http://localhost:5000/api

# CORS
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

### 3. Update backend/Dockerfile
```dockerfile
FROM python:3.11-slim

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

RUN apt-get update && apt-get install -y gcc postgresql-client && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser . .
RUN mkdir -p logs && chown appuser:appuser logs

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 4. Add rate limiting to auth endpoints
```python
# In backend/app/routes/auth_routes.py

from app.utils.middleware import limiter

@router.post("/register")
@limiter.limit("5/minute")
def register(request: Request, user_data: UserRegister, ...):
    pass

@router.post("/login")
@limiter.limit("5/minute")
def login(request: Request, credentials: UserLogin, ...):
    pass

@router.post("/refresh")
@limiter.limit("30/minute")
def refresh_token(request: Request, refresh_token: str, ...):
    pass
```

### 5. Secure cookie configuration
```python
# In backend/app/routes/auth_routes.py

from fastapi.responses import JSONResponse

@router.post("/login")
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    # ... authentication logic ...
    
    response = JSONResponse(content={"message": "Logged in"})
    
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,  # HTTPS only
        samesite="strict",
        max_age=1800  # 30 minutes
    )
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=604800  # 7 days
    )
    
    return response
```

### 6. Remove localStorage from frontend
```javascript
// In frontend/src/services/api.js
// DELETE this:
// api.interceptors.request.use(config => {
//     const token = localStorage.getItem('access_token');
//     if (token) {
//         config.headers.Authorization = `Bearer ${token}`;
//     }
// });

// REPLACE with:
api.interceptors.request.use(config => {
    config.withCredentials = true;  // Send cookies
    return config;
});
```

---

## ✅ Pre-Deployment Checklist

- [ ] Rotate SECRET_KEY and ENCRYPTION_KEY
- [ ] Create .env file with new keys (never commit to git)
- [ ] Update docker-compose.yml to use environment variables
- [ ] Add .env to .gitignore
- [ ] Run `bandit -r backend/app/` for security issues
- [ ] Run `safety check -r requirements.txt` for vulnerable dependencies
- [ ] Test login flow with new HttpOnly cookies
- [ ] Verify CORS whitelist updated for production domain
- [ ] Database backed up
- [ ] Run full test suite
- [ ] Verify rate limiting working
- [ ] Check logs don't contain PII

---

## 🔐 Environment Variable Generation

```bash
# Generate SECRET_KEY (32+ characters)
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"

# Generate ENCRYPTION_KEY (Fernet base64)
python -c "from cryptography.fernet import Fernet; print('ENCRYPTION_KEY=' + Fernet.generate_key().decode())"

# Paste output into .env file
```

---

## 📋 Issues Fixed by File

### backend/app/utils/security.py
- ✅ Issue #1: Remove hardcoded defaults
- ✅ Issue #2: Remove encryption fallback
- ✅ Issue #13: Improve password validation

### backend/app/routes/auth_routes.py
- ✅ Issue #3: Add logout/token revocation
- ✅ Issue #10: Add rate limiting
- ✅ Issue #14: Fix information leakage
- ✅ Issue #15: Sanitize logging

### backend/app/routes/tax_routes.py
- ✅ Issue #8: Add CSRF protection
- ✅ Issue #17: Add error handling for agents

### frontend/src/services/api.js
- ✅ Issue #6: Remove localStorage tokens

### docker-compose.yml & backend/Dockerfile
- ✅ Issue #11: Run as non-root user
- ✅ Issue #12: Move secrets to environment

### backend/app/models/__init__.py
- ✅ Issue #18: Encrypt PAN & phone

---

## 🚀 Next Steps

1. **Immediate** (Today):
   - [ ] Create .env with new secrets
   - [ ] Update hardcoded defaults in security.py
   - [ ] Update docker-compose.yml for environment variables

2. **This Week**:
   - [ ] Add logout endpoint with token revocation
   - [ ] Implement HttpOnly cookies
   - [ ] Add rate limiting to all auth endpoints
   - [ ] Update frontend token handling

3. **Before Production Release**:
   - [ ] Full security audit
   - [ ] Penetration testing
   - [ ] Dependency vulnerability scan
   - [ ] Load testing

