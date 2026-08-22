# Production Deployment Action Plan

## Phase 1: Environment Setup (1-2 Days)

### Step 1.1: Generate Production Secrets

```bash
# Generate SECRET_KEY (64+ characters)
python -c "import secrets; print(secrets.token_urlsafe(64))"
# Copy output to: SECRET_KEY

# Generate ENCRYPTION_KEY (Fernet format)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Copy output to: ENCRYPTION_KEY
```

### Step 1.2: Create Production Environment File

Create `.env.production`:
```env
# Database
DATABASE_URL=postgresql://postgres:YOUR_DB_PASSWORD@db:5432/taxmate_ai
DB_PASSWORD=YOUR_DB_PASSWORD
DB_USER=postgres
DB_NAME=taxmate_ai

# Security (from Step 1.1 above)
SECRET_KEY=YOUR_64_CHAR_SECRET
ENCRYPTION_KEY=YOUR_FERNET_KEY
ENVIRONMENT=production
DEBUG=false

# HTTPS/SSL
SECURE_COOKIES=true
SESSION_COOKIE_SECURE=true
CORS_ORIGINS=https://yourdomain.com

# Frontend
REACT_APP_API_URL=https://yourdomain.com/api

# Monitoring (optional)
SENTRY_DSN=https://your-sentry-dsn
```

### Step 1.3: Create PostgreSQL Backup Script

Create `backend/backup_database.sh`:
```bash
#!/bin/bash
# Daily automated backup script

BACKUP_DIR="/backups/postgresql"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_NAME="taxmate_ai"

mkdir -p $BACKUP_DIR

# Full database backup
pg_dump -U postgres $DB_NAME | gzip > $BACKUP_DIR/backup_${TIMESTAMP}.sql.gz

# Keep last 30 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_DIR/backup_${TIMESTAMP}.sql.gz"

# Optional: Upload to S3
# aws s3 cp $BACKUP_DIR/backup_${TIMESTAMP}.sql.gz s3://your-bucket/backups/
```

**Enable in crontab:**
```bash
# Run daily at 2 AM
0 2 * * * /path/to/backend/backup_database.sh >> /var/log/db_backup.log 2>&1
```

---

## Phase 2: Code Hardening (2-3 Days)

### Step 2.1: Add HTTPS Support

Update `backend/app/main.py`:
```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import os

# Add after CORS middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=os.getenv("ALLOWED_HOSTS", "localhost").split(",")
)

# Update session cookie settings
if os.getenv("ENVIRONMENT") == "production":
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Strict"
```

### Step 2.2: Add Rate Limiting Configuration

Update `backend/app/utils/middleware.py`:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# Rate limiting rules (add to routes):
@app.post("/auth/login")
@limiter.limit("5/minute")  # 5 login attempts per minute
def login():
    pass

@app.post("/api/tax/filings")
@limiter.limit("10/minute")  # 10 filings per minute
def create_filing():
    pass

@app.get("/api/tax/filings")
@limiter.limit("30/minute")  # 30 queries per minute
def get_filings():
    pass
```

### Step 2.3: Add Request Validation

Update `backend/app/schemas/tax_schemas.py`:
```python
from pydantic import BaseModel, Field, validator
from typing import Optional

class IncomeData(BaseModel):
    salary: float = Field(..., ge=0, le=50000000, description="Annual salary")
    interest: float = Field(default=0, ge=0, le=1000000, description="Interest income")
    dividend: float = Field(default=0, ge=0, le=5000000, description="Dividend income")
    
    @validator('salary')
    def salary_not_negative(cls, v):
        if v < 0:
            raise ValueError('Salary cannot be negative')
        return v
```

---

## Phase 3: Testing (3-5 Days)

### Step 3.1: Create Test Suite Structure

```bash
mkdir -p backend/tests/{unit,integration,fixtures}
touch backend/tests/__init__.py
touch backend/tests/conftest.py
```

### Step 3.2: Create Basic Unit Tests

Create `backend/tests/unit/test_auth.py`:
```python
import pytest
from app.utils.security import create_access_token, verify_token
from datetime import timedelta

@pytest.fixture
def test_token():
    return create_access_token(
        data={"sub": "test@example.com"},
        expires_delta=timedelta(minutes=30)
    )

def test_token_creation(test_token):
    assert test_token is not None
    assert len(test_token) > 0

def test_token_verification(test_token):
    claims = verify_token(test_token)
    assert claims["sub"] == "test@example.com"

def test_token_expiration():
    expired_token = create_access_token(
        data={"sub": "test@example.com"},
        expires_delta=timedelta(minutes=-1)
    )
    with pytest.raises(Exception):
        verify_token(expired_token)
```

### Step 3.3: Create Integration Tests

Create `backend/tests/integration/test_auth_flow.py`:
```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_full_auth_flow(client):
    # Register
    register_response = client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "TestPassword123!"
    })
    assert register_response.status_code == 200
    
    # Login
    login_response = client.post("/api/auth/login", json={
        "username": "test@example.com",
        "password": "TestPassword123!"
    })
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()

def test_tax_filing_requires_auth(client):
    # Without token should fail
    response = client.post("/api/tax/filings", json={
        "filing_year": 2024,
        "income_data": {},
        "deductions_data": {}
    })
    assert response.status_code == 401
```

### Step 3.4: Run Tests

```bash
cd backend
pip install pytest pytest-asyncio pytest-cov

# Run all tests
pytest tests/ -v

# With coverage report
pytest tests/ --cov=app --cov-report=html
# Coverage report in: htmlcov/index.html
```

---

## Phase 4: Performance Testing (2-3 Days)

### Step 4.1: Install Load Testing Tools

```bash
pip install locust
```

### Step 4.2: Create Load Test Scenario

Create `locustfile.py`:
```python
from locust import HttpUser, task, between
import json

class TaxMateUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # Login
        response = self.client.post("/api/auth/login", json={
            "username": "test@example.com",
            "password": "password"
        })
        self.client.cookies.update(response.cookies)
    
    @task(3)
    def get_filings(self):
        self.client.get("/api/tax/filings")
    
    @task(1)
    def create_filing(self):
        self.client.post("/api/tax/filings", json={
            "filing_year": 2024,
            "income_data": {
                "salary": 1000000,
                "interest": 50000,
                "dividend": 100000
            },
            "deductions_data": {
                "investments": 150000,
                "health_insurance": 25000
            }
        })
```

### Step 4.3: Run Load Test

```bash
# Web UI on http://localhost:8089
locust -f locustfile.py --host=http://localhost:5000

# OR: Command line with 100 users, 10 spawn rate
locust -f locustfile.py --host=http://localhost:5000 \
    -u 100 -r 10 -t 10m --headless

# Expected results:
# Response time (p50): <200ms
# Response time (p95): <500ms
# Error rate: <1%
```

---

## Phase 5: Production Deployment (1-2 Days)

### Step 5.1: Update Docker Configuration

Update `docker-compose.prod.yml`:
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
      - /backups:/backups  # Backup volume
    restart: always
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build: ./backend
    container_name: taxmate_backend
    ports:
      - "5000:5000"
    environment:
      DATABASE_URL: ${DATABASE_URL}
      SECRET_KEY: ${SECRET_KEY}
      ENCRYPTION_KEY: ${ENCRYPTION_KEY}
      ENVIRONMENT: production
      DEBUG: false
      SECURE_COOKIES: true
    depends_on:
      db:
        condition: service_healthy
    restart: always
    # Performance tuning
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G

  frontend:
    build: ./frontend
    container_name: taxmate_frontend
    ports:
      - "3000:3000"
    environment:
      REACT_APP_API_URL: https://api.yourdomain.com
    depends_on:
      - backend
    restart: always

volumes:
  postgres_data:
```

### Step 5.2: Update Dockerfile for Production

Update `backend/Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Production: Don't use --reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### Step 5.3: Deploy to Staging

```bash
# Pull latest code
git pull origin main

# Create .env.staging
cp .env.example .env.staging
# Edit with staging values

# Deploy
docker-compose -f docker-compose.prod.yml --env-file .env.staging up -d

# Verify services
docker-compose ps
docker-compose logs -f backend

# Check health
curl http://localhost:5000/api/docs
curl http://localhost:5000/health
```

### Step 5.4: Run Smoke Tests in Staging

```bash
# Test registration
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"TestPass123"}'

# Test login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test@example.com","password":"TestPass123"}' \
  -c cookies.txt

# Test tax filing (with token from login)
curl -X GET http://localhost:5000/api/tax/filings \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Step 5.5: Set Up Monitoring

Create `backend/monitoring_setup.sh`:
```bash
#!/bin/bash

# Install Prometheus
docker run -d --name prometheus \
  -p 9090:9090 \
  -v /path/to/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus

# Install Grafana
docker run -d --name grafana \
  -p 3001:3000 \
  -e GF_SECURITY_ADMIN_PASSWORD=admin \
  grafana/grafana

echo "Prometheus: http://localhost:9090"
echo "Grafana: http://localhost:3001"
```

---

## Phase 6: Production Go-Live (1 Day)

### Step 6.1: Final Pre-Production Checklist

```bash
#!/bin/bash
# pre_production_check.sh

echo "📋 Production Pre-Flight Checklist"
echo "=================================="

# Check environment variables
echo "✓ Checking environment variables..."
[ -z "$SECRET_KEY" ] && echo "❌ SECRET_KEY not set" && exit 1
[ -z "$ENCRYPTION_KEY" ] && echo "❌ ENCRYPTION_KEY not set" && exit 1
[ -z "$DATABASE_URL" ] && echo "❌ DATABASE_URL not set" && exit 1
echo "✓ All required environment variables set"

# Check database connection
echo "✓ Testing database connection..."
python -c "import psycopg2; psycopg2.connect('$DATABASE_URL')"
echo "✓ Database connection successful"

# Run tests
echo "✓ Running test suite..."
pytest tests/ -v || exit 1
echo "✓ All tests passed"

# Check dependencies for vulnerabilities
echo "✓ Checking for vulnerable dependencies..."
pip-audit || echo "⚠️  Review any vulnerabilities above"

# Build Docker images
echo "✓ Building Docker images..."
docker-compose -f docker-compose.prod.yml build

echo "✅ All pre-flight checks passed!"
echo "Ready for production deployment"
```

### Step 6.2: Blue-Green Deployment

```bash
#!/bin/bash
# Deploy new version alongside old

# Start "green" (new) environment
docker-compose -f docker-compose.prod.yml -p taxmate_green up -d

# Wait for health checks
sleep 30

# Run smoke tests
curl http://localhost:5000/api/docs || exit 1

# Switch traffic (update load balancer/nginx)
# ... (specific to your infrastructure)

# Keep "blue" running for 1 hour (rollback window)
# Then: docker-compose -p taxmate_blue down
```

### Step 6.3: Production Monitoring

```bash
# Check all services are running
docker-compose ps

# Check logs for errors
docker-compose logs backend | grep -i error

# Monitor performance
curl http://localhost:9090 # Prometheus metrics

# Set up alerts for:
# - CPU > 80%
# - Memory > 85%
# - Error rate > 5%
# - Response time > 1s
```

---

## Phase 7: Post-Deployment Verification (1 Day)

### Step 7.1: Full End-to-End Test

```bash
# Test complete user journey
1. Register new account
2. Login
3. Create tax filing
4. Analyze with all 3 agents
5. Download report
6. Logout
7. Verify token revoked
```

### Step 7.2: Monitor for 24 Hours

- CPU usage stays < 70%
- Memory usage stable
- No unhandled exceptions in logs
- Response times consistent
- Error rate < 1%

### Step 7.3: Update Documentation

- [ ] Update deployment guide with production URLs
- [ ] Document backup/recovery procedures
- [ ] Create incident response runbook
- [ ] Document scaling procedures

---

## Timeline & Resources

```
Week 1: Environment & Security Setup (Phase 1-2)
├─ Day 1: Secrets generation, backup setup
├─ Day 2: HTTPS configuration, rate limiting
└─ Day 3: Request validation enhancements

Week 2: Testing (Phase 3-4)
├─ Day 1-2: Unit tests
├─ Day 3: Integration tests
└─ Day 4-5: Load testing & optimization

Week 3: Staging Deployment (Phase 5)
├─ Day 1-2: Docker configuration
├─ Day 3: Staging deployment
└─ Day 4: Smoke tests & fixes

Week 4: Production (Phase 6-7)
├─ Day 1: Final checks
├─ Day 2: Blue-green deployment
└─ Day 3-4: Monitoring & verification
```

---

## Resources & Links

- [FastAPI Production Deployment](https://fastapi.tiangolo.com/deployment/)
- [PostgreSQL Backup Best Practices](https://www.postgresql.org/docs/current/backup.html)
- [OWASP Top 10 Checklist](https://owasp.org/www-project-top-ten/)
- [Docker Security Best Practices](https://docs.docker.com/develop/security-best-practices/)
- [Locust Load Testing](https://locust.io/)
- [Prometheus Monitoring](https://prometheus.io/)

---

## Questions & Support

If you need help with any step, refer to:
- `PRODUCTION_READINESS_ASSESSMENT.md` - Overall assessment
- `API_REFERENCE.md` - API documentation
- `SETUP.md` - Local development setup
- `TESTING_GUIDE.md` - Testing procedures
