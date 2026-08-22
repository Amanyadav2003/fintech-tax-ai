# TaxMate AI - End-to-End Testing Guide

## Overview
This guide provides comprehensive testing procedures to validate the production-ready TaxMate AI system across all layers: authentication, tax agents, API integration, and frontend UI.

## Pre-Testing Checklist

### Backend Prerequisites
- [ ] PostgreSQL running locally (port 5432)
- [ ] Python 3.11+ installed with venv activated
- [ ] All backend dependencies installed: `pip install -r requirements.txt`
- [ ] `.env.local` configured with:
  - `JWT_SECRET_KEY` (generate: `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
  - `DATABASE_URL=postgresql://postgres:password@localhost:5432/taxmate_ai`
  - `SENTRY_DSN` (optional, can use dummy value for testing)

### Frontend Prerequisites
- [ ] Node.js 16+ and npm installed
- [ ] Frontend dependencies installed: `npm install` in `/frontend`
- [ ] `REACT_APP_API_URL=http://localhost:5000/api` in `.env.local`

### Docker (Optional)
- [ ] Docker and Docker Compose installed
- [ ] Can run: `docker-compose up -d` instead of manual services

---

## 1. Authentication Flow Testing

### 1.1 Backend JWT Setup
**Test: JWT Token Generation & Verification**

```bash
# From /backend directory
python -c "
from app.utils.security import create_access_token, verify_token
from datetime import timedelta

# Create token
token = create_access_token({'sub': 'test@example.com'}, timedelta(minutes=30))
print(f'Token: {token}')

# Verify token
claims = verify_token(token)
print(f'Claims: {claims}')
"
```
Expected: Token generated, claims extracted correctly ✓

### 1.2 Database Setup
**Test: Create Database & Apply Schema**

```bash
# Create database (if not exists)
createdb taxmate_ai -U postgres

# From /backend, run migrations (if Alembic is set up)
# For now, models will auto-create on first FastAPI run
```
Expected: No errors, tables created ✓

### 1.3 Backend Service Start
**Test: Start FastAPI Server**

```bash
cd /backend
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
```
Expected: Server starts, logs show "Uvicorn running on http://0.0.0.0:5000" ✓

### 1.4 Health Check Endpoint
**Test: Verify API is responsive**

```bash
curl http://localhost:5000/health
```
Expected: `{"status": "ok"}` ✓

### 1.5 User Registration
**Test: Register new user**

```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass@123",
    "pan": "ABCDE1234F",
    "phone": "9876543210",
    "age": 35,
    "state": "Maharashtra"
  }'
```
Expected: HTTP 201, returns `{"id": 1, "email": "test@example.com", "message": "User registered"}`
Failure modes to check:
  - [ ] Missing field: 400 error with validation details
  - [ ] Duplicate email: 409 Conflict
  - [ ] Invalid PAN (not 10 chars): 400 error
  - [ ] Password too weak: 400 error

### 1.6 User Login
**Test: Login and get JWT tokens**

```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass@123"
  }'
```
Expected: HTTP 200, returns:
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800
}
```
Failure modes:
  - [ ] Invalid email: 401 Unauthorized
  - [ ] Invalid password: 401 Unauthorized
  - [ ] Non-existent user: 401 Unauthorized

### 1.7 Token Refresh
**Test: Refresh expired access token**

```bash
curl -X POST http://localhost:5000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "<from_login_response>"
  }'
```
Expected: HTTP 200, returns new access_token ✓

### 1.8 Get Current User Profile
**Test: Access protected endpoint**

```bash
curl http://localhost:5000/api/auth/me \
  -H "Authorization: Bearer <access_token>"
```
Expected: HTTP 200, returns user profile ✓
Failure modes:
  - [ ] No Authorization header: 403 Forbidden
  - [ ] Invalid token: 401 Unauthorized
  - [ ] Expired token: 401 Unauthorized

---

## 2. Tax Agent Testing

### 2.1 Tax Agent - Basic Calculation
**Test: Verify ITR tax calculation (Old vs New Regime)**

```bash
# From /backend, run:
python test_agents.py
```
Expected output shows:
```
TAX AGENT RESULTS:
Gross Income: 1200000
Total Deductions: 150000
Taxable Income: 1050000
Old Regime Tax: 157500
New Regime Tax: 140000
Recommended: Old Regime
```
Check:
  - [ ] Old regime tax > new regime tax (deductions benefit)
  - [ ] Tax calculation matches manual calculation
  - [ ] Regime recommendation is correct

### 2.2 Risk Agent - Audit Risk Scoring
**Test: Verify audit risk detection and benchmarking**

```bash
# In test_agents.py output, look for:
RISK AGENT RESULTS:
Audit Risk Score: 4/10 (GREEN)
Flags: [...]
Penalty if Audited: 5000
```
Check:
  - [ ] Score is 0-10
  - [ ] Green (0-3), Yellow (3-7), or Red (7-10)
  - [ ] Benchmarking results shown (p50, p75, p90)
  - [ ] Penalty calculation makes sense

### 2.3 Strategy Agent - Recommendations
**Test: Verify tax strategy recommendations**

Look for output like:
```
STRATEGY AGENT RESULTS:
Financial Health Score: 72/100
Missed Opportunities: [...]
Recommended Actions: [...]
```
Check:
  - [ ] Health score 0-100
  - [ ] Recommendations are specific and actionable
  - [ ] Actions ranked by priority and impact

---

## 3. API Integration Testing

### 3.1 Create Tax Filing
**Test: Create new tax filing record**

```bash
ACCESS_TOKEN="<from_login>"

curl -X POST http://localhost:5000/api/tax/filings \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "filing_year": 2024,
    "income_data": {
      "salary": 1200000,
      "interest": 50000,
      "dividend": 100000,
      "rental": 0,
      "professional_fees": 0
    },
    "deductions_data": {
      "investments": 150000,
      "health_insurance": 25000,
      "education_loan_interest": 0,
      "home_loan_interest": 0,
      "donations": 0,
      "medical_expenses": 0
    },
    "tds_paid": 0,
    "advance_tax_paid": 0
  }'
```
Expected: HTTP 201, returns `{"id": 1, "user_id": 1, "filing_year": 2024, ...}`

### 3.2 Run Tax Analysis (All Agents)
**Test: Execute all 3 agents and get combined results**

```bash
FILING_ID="<from_previous_response>"

curl -X POST http://localhost:5000/api/tax/analyze/$FILING_ID \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```
Expected: HTTP 200, returns:
```json
{
  "filing_id": 1,
  "tax_analysis": {
    "gross_income": 1350000,
    "total_deductions": 175000,
    "taxable_income": 1175000,
    "old_regime_tax": 180625,
    "new_regime_tax": 163000,
    "recommended_regime": "Old"
  },
  "risk_analysis": {
    "audit_risk_score": 4,
    "flags": [...],
    "penalty_if_audited": 5000
  },
  "strategy_analysis": {
    "financial_health_score": 72,
    "missed_opportunities": [...],
    "recommended_actions": [...]
  }
}
```

### 3.3 Rate Limiting
**Test: Verify 10 requests/minute limit**

```bash
# Make 11 requests rapidly to /api/tax/analyze/{filing_id}
for i in {1..11}; do
  curl -X POST http://localhost:5000/api/tax/analyze/$FILING_ID \
    -H "Authorization: Bearer $ACCESS_TOKEN"
done
```
Expected: 10th request succeeds, 11th returns HTTP 429 (Too Many Requests) ✓

### 3.4 CORS Security
**Test: Verify CORS headers**

```bash
curl -i -X OPTIONS http://localhost:5000/api/tax/filings \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST"
```
Expected: Response includes `Access-Control-Allow-Origin: http://localhost:3000` ✓

---

## 4. Frontend Testing

### 4.1 Start Frontend Dev Server
**Test: React app loads**

```bash
cd /frontend
npm start
```
Expected: App opens at http://localhost:3000 ✓

### 4.2 Registration Flow
**Test: New user registration**

1. [ ] Page shows "Begin your tax filing journey"
2. [ ] Enter: email, password (with strength indicator), PAN, phone, age, state
3. [ ] Click "Register"
4. [ ] See "Registration successful! Please log in."
5. [ ] Form switches to login mode

### 4.3 Login Flow
**Test: User login**

1. [ ] Enter registered email and password
2. [ ] Click "Login"
3. [ ] Token stored in localStorage
4. [ ] Redirected to Income form
5. [ ] User email shown in header
6. [ ] Progress indicator shows "Income" step active

### 4.4 Income Form
**Test: Income data entry**

1. [ ] Enter all income sources
2. [ ] See total gross income calculated
3. [ ] Income in ₹5L-₹25L range shows green checkmark
4. [ ] Click "Next: Add Deductions →"
5. [ ] Deductions form loads

### 4.5 Deductions Form
**Test: Deduction data entry**

1. [ ] Enter deductions for each category
2. [ ] 80C max value enforced (can't exceed ₹1.5L)
3. [ ] See total deductions calculated
4. [ ] Click "Analyze My Taxes →"
5. [ ] Loading state shown ("Analyzing...")

### 4.6 Results Display
**Test: Tax analysis results shown**

1. [ ] Results page loads
2. [ ] See all 3 sections:
   - [ ] Tax Computation (GTI, Deductions, Taxable Income)
   - [ ] Old vs New Regime comparison
   - [ ] Audit Risk score (with color-coded risk level)
   - [ ] Financial Health score
   - [ ] Missed opportunities list
   - [ ] Recommended actions (ranked)
3. [ ] Disclaimer visible at bottom
4. [ ] "New Analysis" and "Download Report" buttons shown

### 4.7 Error Handling
**Test: Error messages displayed**

1. [ ] Log out, then delete access_token from localStorage
2. [ ] Try to access any protected route
3. [ ] Should redirect to login with message "Not logged in"
4. [ ] Network error: Should show "Error: Network request failed"
5. [ ] Server error: Should show specific error message from API

### 4.8 Session Persistence
**Test: Login persists across page reload**

1. [ ] Register and login
2. [ ] Hard refresh page (Ctrl+Shift+R)
3. [ ] Should still be logged in
4. [ ] Should not require re-login
5. [ ] User email still showing in header

### 4.9 Logout Flow
**Test: Logout clears session**

1. [ ] Click "Logout" button in header
2. [ ] Redirected to login/register page
3. [ ] localStorage cleared (tokens and email removed)
4. [ ] Can log back in

### 4.10 Mobile Responsiveness
**Test: Works on mobile viewport**

1. [ ] Open DevTools → Toggle device toolbar
2. [ ] Test on iPhone 12 (390x844)
3. [ ] All forms readable and clickable
4. [ ] Progress indicator adapts
5. [ ] Results cards stack vertically
6. [ ] Buttons full width or properly spaced

---

## 5. Integration End-to-End Flow

### Complete User Journey
1. [ ] User opens app at localhost:3000
2. [ ] Registers with new email
3. [ ] Logs in successfully
4. [ ] Enters income (₹10L salary)
5. [ ] Enters deductions (₹1.5L 80C)
6. [ ] Clicks "Analyze My Taxes"
7. [ ] Sees results within 5 seconds
8. [ ] Results show reasonable numbers
9. [ ] Tries "New Analysis"
10. [ ] Goes back to Income form (not login)
11. [ ] Changes income, reanalyzes
12. [ ] Clicks logout
13. [ ] Back to login page

**Expected**: All steps complete without errors ✓

---

## 6. Security Testing

### 6.1 Password Hashing
**Test: Passwords are bcrypt hashed**

```bash
# Query database
psql taxmate_ai -U postgres -c "SELECT email, LENGTH(hashed_password) FROM \"user\" LIMIT 1;"
```
Expected: hashed_password is 60 characters (bcrypt hash) ✓

### 6.2 Sensitive Data Encryption
**Test: PAN field is encrypted**

```bash
# Query database
psql taxmate_ai -U postgres -c "SELECT pan FROM \"user\" LIMIT 1;"
```
Expected: pan shows encrypted bytes (not plaintext) ✓

### 6.3 Token Cannot Access Other Users' Data
**Test: User A's token can't access User B's data**

1. [ ] Register User A (test1@example.com)
2. [ ] Register User B (test2@example.com)
3. [ ] Login as User A, get token A
4. [ ] Create filing as User A (filing_id=1)
5. [ ] Login as User B, get token B
6. [ ] Try to access filing_id=1 with token B
7. [ ] Should get 403 Forbidden or 404 Not Found

### 6.4 Invalid Token Rejection
**Test: Invalid/expired tokens rejected**

```bash
curl http://localhost:5000/api/auth/me \
  -H "Authorization: Bearer invalid.token.here"
```
Expected: HTTP 401 Unauthorized ✓

### 6.5 SQL Injection Prevention
**Test: Pydantic validation prevents SQL injection**

```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test\"; DROP TABLE user; --@example.com",
    "password": "Test@123456",
    "pan": "ABCDE1234F",
    "phone": "9876543210",
    "age": 25,
    "state": "Maharashtra"
  }'
```
Expected: HTTP 400 validation error (invalid email format), table not dropped ✓

---

## 7. Performance Testing

### 7.1 API Response Time
**Test: Analyze endpoint responds within acceptable time**

```bash
curl -w "\nTime: %{time_total}s\n" \
  -X POST http://localhost:5000/api/tax/analyze/1 \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```
Expected: Response < 2 seconds ✓

### 7.2 Database Query Performance
**Test: Queries use indexes efficiently**

```bash
# Enable query logging
psql taxmate_ai -U postgres -c "SET log_statement = 'all';"

# Run tax analysis
# Check logs for full table scans (EXPLAIN ANALYZE)
```
Expected: No sequential scans on large tables ✓

---

## 8. Browser DevTools Testing

### 8.1 Network Tab
1. [ ] Open Chrome DevTools → Network tab
2. [ ] Perform login
3. [ ] Check requests:
   - [ ] POST /api/auth/login → 200
   - [ ] Check response headers for CORS headers
   - [ ] Check request has `Content-Type: application/json`

### 8.2 Application Tab (Storage)
1. [ ] Open DevTools → Application → Local Storage
2. [ ] After login, verify stored:
   - [ ] access_token (JWT starting with "eyJ")
   - [ ] refresh_token (JWT)
   - [ ] user_email (user's email)

### 8.3 Console
1. [ ] No errors or warnings
2. [ ] Run: `console.log(localStorage.getItem('access_token'))` → shows token
3. [ ] No unhandled promise rejections

---

## 9. Docker Testing (Optional)

### 9.1 Docker Compose Stack
**Test: All services start correctly**

```bash
docker-compose up -d
```
Check logs:
```bash
docker-compose logs -f backend  # Should show uvicorn running
docker-compose logs -f frontend # Should show app running
```

### 9.2 Services Communication
```bash
# From inside container
docker exec -it taxmate_backend curl http://localhost:5000/health
```
Expected: Returns health status ✓

---

## 10. Debugging Checklist

### Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| "Cannot GET /api/..." | Backend not running | `uvicorn app.main:app --reload` |
| "CORS error" | Frontend different port | Check ALLOWED_ORIGINS in .env.local |
| "401 Unauthorized" | Token expired | Refresh token or re-login |
| "Database connection error" | PostgreSQL not running | `psql` should connect to localhost:5432 |
| "npm ERR! module not found" | Dependencies not installed | `npm install` in /frontend |
| "No module named 'app'" | Python path issue | Run from /backend directory |
| "Slow API response" | Query performance | Check Sentry for slow queries |

---

## 11. Load Testing (Optional)

### Quick Load Test with Apache Bench
```bash
ab -n 100 -c 10 http://localhost:5000/health
```
Expected: 100 requests completed with < 1% errors ✓

---

## Reporting Test Results

Create a test report with:
- [ ] Date & time of testing
- [ ] Environment (local, staging, prod)
- [ ] Browser version
- [ ] Python version
- [ ] Node version
- [ ] Any failures and remediation steps
- [ ] Sign-off from QA

---

## Production Deployment Checklist

Before deploying to production:
- [ ] All tests above pass
- [ ] Generate new JWT_SECRET_KEY
- [ ] Set SENTRY_DSN to real Sentry project
- [ ] Database backups configured
- [ ] SSL/HTTPS enabled
- [ ] ALLOWED_ORIGINS updated to production domains
- [ ] Rate limiting tuned for expected traffic
- [ ] Monitoring dashboards set up
- [ ] Incident response plan documented
- [ ] Security audit completed

---

**Last Updated**: 2024
**Test Coverage**: End-to-End (Auth → Tax Analysis → Results)
**Expected Pass Rate**: 100%
