# Database Setup Guide for TaxMate AI

## Overview

This guide covers complete database setup including PostgreSQL configuration, table creation, and verification.

---

## Prerequisites

- Python 3.8+
- PostgreSQL 12+ (local or Docker)
- Required Python packages (should be in requirements.txt):
  - sqlalchemy
  - psycopg2-binary
  - python-dotenv

---

## Quick Start (3 Steps)

### Step 1: Configure Environment Variables

Update `backend/.env` with your database credentials:

```bash
cd backend

# Copy example file
cp .env.example .env

# Edit .env and replace:
# - DB_PASSWORD: Use a secure password (20+ characters)
# - SECRET_KEY: Generate using: python -c "import secrets; print(secrets.token_urlsafe(32))"
# - ENCRYPTION_KEY: Generate using: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

**Example .env file:**
```
DATABASE_URL=postgresql://postgres:YourSecurePassword123@localhost:5432/taxmate_ai
DB_USER=postgres
DB_PASSWORD=YourSecurePassword123
DB_HOST=localhost
DB_PORT=5432
DB_NAME=taxmate_ai
SECRET_KEY=your_generated_secret_key_here
ENCRYPTION_KEY=your_generated_encryption_key_here
```

### Step 2: Ensure PostgreSQL is Running

**Option A: Using Docker Compose (Recommended)**
```bash
# Start PostgreSQL container
docker-compose up db -d
# Wait 10 seconds for it to be ready
sleep 10
```

**Option B: Using Local PostgreSQL**
```bash
# On Windows
# Make sure PostgreSQL service is running
# Or start it: net start postgresql-x64-15

# On macOS
brew services start postgresql

# On Linux
sudo systemctl start postgresql
```

**Verify PostgreSQL is running:**
```bash
psql -U postgres -h localhost -c "SELECT version();"
# Should return PostgreSQL version
```

### Step 3: Run Database Setup Script

```bash
cd backend
python setup_database.py
```

**Expected output:**
```
✅ Checking environment configuration...
✅ Environment configuration validated
ℹ️  Connecting to PostgreSQL...
✅ Connected to PostgreSQL
ℹ️  Creating database 'taxmate_ai'...
✅ Database created successfully
ℹ️  Connecting to application database...
✅ Connected to application database
ℹ️  Creating application tables...
✅ All tables created successfully
ℹ️  Verifying table creation...
✅ users (11 columns)
✅ tax_filings (18 columns)
✅ audit_flags (6 columns)
✅ benchmark_data (8 columns)
✅ token_blacklist (5 columns)

✅ Database setup completed successfully!
```

---

## Manual Database Setup (If Script Fails)

### Method 1: Using psql Command Line

```bash
# Connect to PostgreSQL
psql -U postgres -h localhost

# Create database
CREATE DATABASE taxmate_ai;

# Create user (optional, if not using postgres)
CREATE USER taxmate WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE taxmate_ai TO taxmate;

# Verify creation
\l  # List databases
\q  # Quit
```

### Method 2: Using Python Directly

```bash
cd backend
python
```

Then in Python shell:

```python
from app.utils.database import engine, init_db
from app.models import Base

# Create all tables
init_db()

# Verify
from sqlalchemy import inspect
inspector = inspect(engine)
print("Tables created:", inspector.get_table_names())
```

---

## Database Schema

### Table: users
Stores user account information
```
- id (Primary Key)
- email (Unique)
- name
- phone
- pan (Unique, encrypted in production)
- password_hash
- age
- state
- is_active (Boolean)
- is_verified (Boolean)
- verification_token
- created_at
- updated_at
```

### Table: tax_filings
Stores tax filing records
```
- id (Primary Key)
- user_id (Foreign Key)
- filing_year
- status (draft, completed, filed)
- salary, interest, dividend, rental_income, professional_fees
- total_income
- investments_80c, health_insurance_80d, education_loan_80e, home_loan_interest_80emi, donations_80g
- other_deductions, total_deductions
- taxable_income
- tax_old_regime, tax_new_regime
- recommended_regime
- tds_paid, advance_tax_paid
- tax_agent_output (JSON)
- risk_agent_output (JSON)
- strategy_agent_output (JSON)
- created_at, updated_at
```

### Table: audit_flags
Stores potential audit risks
```
- id (Primary Key)
- filing_id
- flag_type
- severity (low, medium, high)
- description
- recommendation
- created_at
```

### Table: benchmark_data
Stores tax benchmarking data
```
- id (Primary Key)
- income_bracket_min, income_bracket_max
- deduction_type
- median_amount, mean_amount
- percentile_75, percentile_90
- audit_risk_percentage
- year
```

### Table: token_blacklist
Stores revoked JWT tokens
```
- id (Primary Key)
- token_jti (Unique) - JWT ID claim
- user_id
- blacklisted_at
- expires_at
```

---

## Connection Strings

### Development (Local PostgreSQL)
```
postgresql://postgres:password@localhost:5432/taxmate_ai
```

### Docker Compose
```
postgresql://postgres:password@db:5432/taxmate_ai
```

### Production (AWS RDS example)
```
postgresql://user:password@my-db.abc123.us-east-1.rds.amazonaws.com:5432/taxmate_ai
```

---

## Testing Database Connection

### Option 1: Using Python Script
```bash
cd backend
python -c "
from app.utils.database import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        result = conn.execute(text('SELECT NOW()'))
        print('✅ Database connection successful!')
        print('Current time:', result.scalar())
except Exception as e:
    print('❌ Connection failed:', e)
"
```

### Option 2: Using psql
```bash
psql -U postgres -h localhost -d taxmate_ai -c "SELECT COUNT(*) as user_count FROM users;"
```

### Option 3: Using the Application
```bash
cd backend
uvicorn app.main:app --reload
# App starts successfully = database is connected
```

---

## Database Maintenance

### Backup Database
```bash
# Backup to file
pg_dump -U postgres -h localhost -d taxmate_ai > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore from file
psql -U postgres -h localhost -d taxmate_ai < backup_file.sql
```

### Reset Database (CAUTION: Deletes all data)
```bash
# Connect as postgres
psql -U postgres -h localhost

# Drop and recreate
DROP DATABASE taxmate_ai;
CREATE DATABASE taxmate_ai;
\q

# Re-run setup
python setup_database.py
```

### View Database Logs
```bash
# Docker
docker-compose logs db

# Local PostgreSQL (PostgreSQL logs directory)
tail -f /var/log/postgresql/postgresql.log  # Linux
# macOS: ~/Library/Logs/postgres.log
```

---

## Common Issues & Solutions

### Issue: "Connection refused"
**Solution**: 
- Ensure PostgreSQL is running
- Check host/port are correct in .env
- Check username/password are correct

### Issue: "Database does not exist"
**Solution**:
```bash
python setup_database.py  # Automatically creates database
# or manually: CREATE DATABASE taxmate_ai;
```

### Issue: "Permission denied"
**Solution**:
```bash
# Grant permissions to user
psql -U postgres -h localhost
ALTER USER postgres WITH SUPERUSER;
# or create new user with permissions
CREATE USER taxmate WITH ENCRYPTED PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE taxmate_ai TO taxmate;
```

### Issue: "Port 5432 already in use"
**Solution**:
- Change port in .env: `DATABASE_URL=postgresql://postgres:password@localhost:5433/taxmate_ai`
- Or stop existing PostgreSQL: `docker-compose down`

### Issue: "SSL connection error"
**Solution**: Add to connection string:
```
postgresql://user:password@host:5432/db?sslmode=disable
```
(Note: Only for development, enable SSL in production)

---

## Environment Variables Reference

| Variable | Required | Example | Description |
|----------|----------|---------|-------------|
| DATABASE_URL | Yes | postgresql://user:pass@localhost/db | Full connection string |
| DB_USER | Yes | postgres | Database user |
| DB_PASSWORD | Yes | secure_pass_123 | Database password |
| DB_HOST | No | localhost | Database host (default: localhost) |
| DB_PORT | No | 5432 | Database port (default: 5432) |
| DB_NAME | Yes | taxmate_ai | Database name |
| SECRET_KEY | Yes | [generated] | JWT secret key |
| ENCRYPTION_KEY | Yes | [generated] | Fernet encryption key |

---

## Performance Tips

### Create Indexes (for production)
```sql
-- User queries
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_pan ON users(pan);

-- Filing queries
CREATE INDEX idx_filings_user_id ON tax_filings(user_id);
CREATE INDEX idx_filings_year ON tax_filings(filing_year);

-- Token queries
CREATE INDEX idx_tokens_jti ON token_blacklist(token_jti);
CREATE INDEX idx_tokens_user_id ON token_blacklist(user_id);
CREATE INDEX idx_tokens_expires ON token_blacklist(expires_at);
```

### Connection Pool Settings
In `database.py`:
```python
engine = create_engine(
    DATABASE_URL,
    pool_size=10,           # Number of connections to keep
    max_overflow=20,        # Additional connections if needed
    pool_pre_ping=True,     # Test connections before use
    pool_recycle=3600       # Recycle connections hourly
)
```

---

## Production Checklist

- [ ] Use strong database password (20+ characters)
- [ ] Enable SSL/TLS for database connection
- [ ] Regular automated backups configured
- [ ] Database monitoring enabled
- [ ] Connection pool optimized
- [ ] Indexes created for common queries
- [ ] Query logging enabled for debugging
- [ ] User permissions restricted (no superuser account)
- [ ] Database in private VPC/network
- [ ] Encryption at rest enabled (if using cloud DB)

---

## Support

For issues or questions:
1. Check the "Common Issues" section above
2. Review PostgreSQL logs: `docker-compose logs db`
3. Test connection: Run the test script in "Testing Database Connection"
4. Check .env configuration matches expected format

---

**Last Updated**: April 26, 2026  
**Status**: Ready for production setup
