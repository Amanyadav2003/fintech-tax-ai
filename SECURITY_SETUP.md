# Security Setup Guide

This document covers the security fixes applied to the TaxMate AI application and how to set them up.

## Critical Security Fixes Implemented

### 1. ✅ Hardcoded Secrets Removed
- **Fixed**: Removed default values from `SECRET_KEY` and `ENCRYPTION_KEY`
- **Status**: Environment variables are now mandatory
- **Action**: Configure `.env` file before running the application

### 2. ✅ Encryption Implementation Hardened
- **Fixed**: Encryption now fails fast instead of falling back to plaintext
- **Status**: Sensitive data (PAN, SSN, etc.) will never be stored unencrypted
- **Action**: Ensure `ENCRYPTION_KEY` is properly configured

### 3. ✅ Token Revocation & Logout Implemented
- **Fixed**: Added `TokenBlacklist` model for tracking revoked tokens
- **Fixed**: Login endpoint now sets HttpOnly cookies instead of returning tokens
- **Fixed**: New `/logout` endpoint properly invalidates sessions
- **Action**: Run database migration to create `token_blacklist` table

### 4. ✅ HttpOnly Cookies for Token Storage
- **Fixed**: Access tokens stored in HttpOnly cookies (cannot be read by JavaScript)
- **Fixed**: Frontend no longer uses localStorage (XSS vulnerability fixed)
- **Status**: Browser automatically manages cookie transmission
- **Action**: None - automatic with updated code

### 5. ✅ CORS Configuration Restricted
- **Fixed**: CORS now allows specific headers only (`Content-Type`, `Authorization`)
- **Fixed**: CORS origins restricted to configured domains
- **Action**: Set `CORS_ORIGINS` in `.env`

### 6. ✅ Docker Secrets Management
- **Fixed**: No hardcoded secrets in `docker-compose.yml`
- **Fixed**: All secrets loaded from environment variables
- **Action**: Create `.env` file with required variables before docker-compose up

---

## Setup Instructions

### Step 1: Generate Security Keys

```bash
# Generate SECRET_KEY (32+ character random string)
python -c "import secrets; key = secrets.token_urlsafe(32); print(f'SECRET_KEY={key}')"

# Generate ENCRYPTION_KEY (Fernet key)
python -c "from cryptography.fernet import Fernet; key = Fernet.generate_key().decode(); print(f'ENCRYPTION_KEY={key}')"
```

### Step 2: Create .env File

Copy `.env.example` to `.env` and fill in the generated values:

```bash
cp .env.example .env
# Edit .env with your generated SECRET_KEY and ENCRYPTION_KEY
```

Example `.env`:
```
DATABASE_URL=postgresql://postgres:YourSecurePassword@localhost:5432/taxmate_ai
DB_USER=postgres
DB_PASSWORD=YourSecurePassword
DB_NAME=taxmate_ai
SECRET_KEY=GeneratedSecretKeyHere
ENCRYPTION_KEY=GeneratedEncryptionKeyHere
CORS_ORIGINS=http://localhost:3000
ENVIRONMENT=development
```

### Step 3: Database Setup

The `TokenBlacklist` table is required for token revocation. Create it with:

```sql
CREATE TABLE token_blacklist (
    id SERIAL PRIMARY KEY,
    token_jti VARCHAR UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    blacklisted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    INDEX idx_jti (token_jti),
    INDEX idx_user_id (user_id),
    INDEX idx_blacklisted_at (blacklisted_at)
);
```

Or run through SQLAlchemy:
```bash
cd backend
python -c "from app.utils.database import engine; from app.models import Base; Base.metadata.create_all(bind=engine)"
```

### Step 4: Run Application

```bash
# Using Docker Compose
docker-compose up

# Or locally with Python
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

---

## Security Improvements Summary

| Issue | Before | After |
|-------|--------|-------|
| Secret Storage | Hardcoded defaults in code | Environment variables (mandatory) |
| Encryption Failure | Falls back to plaintext | Fails with error |
| Token Revocation | Not possible (tokens valid forever) | Implemented with logout |
| Token Storage | localStorage (XSS vulnerable) | HttpOnly cookies |
| CORS Headers | Wildcard (*) | Specific headers only |
| Docker Secrets | Hardcoded in compose file | Environment variables |

---

## Testing the Security Fixes

### 1. Test HttpOnly Cookies

```bash
# Login and check cookies (should not see tokens in localStorage)
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}'

# Check browser cookies (tokens should be HttpOnly, not in localStorage)
# Open DevTools → Application → Cookies
```

### 2. Test Logout Revocation

```bash
# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}'

# Logout (clears cookies and blacklists tokens)
curl -X POST http://localhost:5000/api/auth/logout \
  -b "access_token=..." -b "refresh_token=..."

# Try to use revoked token (should fail)
curl -X GET http://localhost:5000/api/tax/filings \
  -b "access_token=..."  # Should return 401
```

### 3. Test CORS Restrictions

```bash
# This should work (allowed origin)
curl -X OPTIONS http://localhost:5000/api/auth/login \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST"

# This should be blocked (not in CORS_ORIGINS)
curl -X OPTIONS http://localhost:5000/api/auth/login \
  -H "Origin: http://attacker.com" \
  -H "Access-Control-Request-Method: POST"
```

---

## Production Checklist

Before deploying to production:

- [ ] Set `SECURE_COOKIES=true` (requires HTTPS)
- [ ] Use strong `SECRET_KEY` (64+ characters recommended)
- [ ] Use strong `DB_PASSWORD` (20+ characters)
- [ ] Set `ENVIRONMENT=production`
- [ ] Set `CORS_ORIGINS` to your actual domain(s)
- [ ] Enable HTTPS (required for secure cookies)
- [ ] Set up automated .env backup
- [ ] Enable database backups
- [ ] Set `SENTRY_DSN` for error tracking
- [ ] Implement rate limiting configuration
- [ ] Test all authentication flows
- [ ] Set up log monitoring

---

## Troubleshooting

### Secret validation fails on startup
- Check `.env` file exists and contains `SECRET_KEY` and `ENCRYPTION_KEY`
- Ensure keys are at least 32 characters
- Verify `ENCRYPTION_KEY` is a valid Fernet key

### Tokens not persisting between requests
- Check that `withCredentials: true` is set in axios
- Verify cookies are not being blocked
- Check CORS `allow_credentials=True` is set

### Cannot decrypt saved data
- Verify `ENCRYPTION_KEY` hasn't changed
- Ensure data was encrypted with the same key
- Check encryption_key format is valid Fernet

---

## Security Resources

- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [OWASP Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)
- [HTTP Cookies Security](https://tools.ietf.org/html/rfc6265bis)
- [Fernet - Symmetric Encryption](https://cryptography.io/en/latest/fernet/)
