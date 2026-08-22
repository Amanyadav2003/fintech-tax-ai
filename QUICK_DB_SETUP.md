# Database Setup - Quick Reference Card

## 🚀 Fast Track (5 minutes)

```bash
# 1. Configure environment
cd backend
cp .env.example .env
# Edit .env: change DB_PASSWORD, SECRET_KEY, ENCRYPTION_KEY

# 2. Start PostgreSQL (choose one)
docker-compose up db -d    # Option A: Docker
# OR
# Option B: Make sure local PostgreSQL is running

# 3. Run setup script
python setup_database.py

# 4. Verify
psql -U postgres -h localhost -d taxmate_ai -c "SELECT COUNT(*) FROM users;"

# 5. Done! ✅
```

---

## 📋 Step-by-Step with Details

### Step 1: Update .env File
```bash
cd backend

# Copy template
cp .env.example .env

# Edit these values in .env:
DB_PASSWORD=YourSecurePassword123      # Use strong password
SECRET_KEY=[generated value]           # Generate: python -c "import secrets; print(secrets.token_urlsafe(32))"
ENCRYPTION_KEY=[generated value]       # Generate: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Example .env:
# DATABASE_URL=postgresql://postgres:YourSecurePassword123@localhost:5432/taxmate_ai
# DB_PASSWORD=YourSecurePassword123
# SECRET_KEY=xyz...
# ENCRYPTION_KEY=abc...
```

### Step 2: Start PostgreSQL
```bash
# Option A: Docker Compose (Recommended)
docker-compose up db -d
sleep 10  # Wait for container to start

# Option B: Local Installation
# Windows: PostgreSQL should be running as service
# macOS: brew services start postgresql
# Linux: sudo systemctl start postgresql

# Verify:
psql -U postgres -h localhost -c "SELECT 1;"
```

### Step 3: Run Database Setup
```bash
cd backend
python setup_database.py

# Expected output:
# ✅ Checking environment configuration...
# ✅ Connected to PostgreSQL
# ✅ Database created successfully
# ✅ All tables created successfully
# ✅ Database setup completed successfully!
```

### Step 4: Verify Setup
```bash
# Option 1: Check tables exist
psql -U postgres -h localhost -d taxmate_ai -c "\dt"

# Option 2: Check specific table
psql -U postgres -h localhost -d taxmate_ai -c "SELECT * FROM users LIMIT 1;"

# Option 3: Python verification
python -c "
from app.utils.database import engine
from sqlalchemy import inspect
inspector = inspect(engine)
print('Tables:', inspector.get_table_names())
"
```

---

## 🔑 Environment Variables Required

```env
# CRITICAL (Must be configured)
DB_PASSWORD=<strong_password>           # 20+ characters
SECRET_KEY=<generated_key>              # 32+ characters
ENCRYPTION_KEY=<generated_key>          # Fernet key

# Database Connection
DATABASE_URL=postgresql://postgres:password@localhost:5432/taxmate_ai
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_NAME=taxmate_ai

# Application Settings
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:3001
REACT_APP_API_URL=http://localhost:5000/api
```

---

## 📊 Database Tables Created

```
users                    - User accounts (11 columns)
tax_filings              - Tax filing records (18 columns)
audit_flags              - Audit risk flags (6 columns)
benchmark_data           - Benchmark data (8 columns)
token_blacklist          - Revoked tokens (5 columns)
```

---

## ✅ Verification Checklist

```bash
# 1. Can connect to database?
psql -U postgres -h localhost -d taxmate_ai -c "SELECT 1;"
# Expected: (1 row)

# 2. Do all tables exist?
psql -U postgres -h localhost -d taxmate_ai -c "\dt"
# Expected: 5 tables listed

# 3. Is token_blacklist table created?
psql -U postgres -h localhost -d taxmate_ai -c "\d token_blacklist"
# Expected: Table structure shown

# 4. Can application connect?
cd backend
python -c "from app.utils.database import engine; engine.connect()"
# Expected: No error
```

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| Connection refused | Start PostgreSQL: `docker-compose up db -d` |
| Database doesn't exist | Run: `python setup_database.py` |
| Permission denied | Check DB_PASSWORD in .env |
| Tables don't exist | Run: `python setup_database.py` again |
| Port 5432 in use | Change port in .env or stop other PostgreSQL |
| .env file missing | Create: `cp .env.example .env` |

---

## 🚀 Next Steps

After database is ready:

```bash
# 1. Install dependencies (if not done)
pip install -r requirements.txt

# 2. Generate required keys (if not done)
python -c "import secrets; print(secrets.token_urlsafe(32))"
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# 3. Update .env with generated keys
# (Edit backend/.env file)

# 4. Test application
cd backend
uvicorn app.main:app --reload

# 5. Or use Docker Compose
docker-compose up

# Application ready at:
# Backend: http://localhost:5000
# Frontend: http://localhost:3001
# API Docs: http://localhost:5000/api/docs
```

---

## 🔗 Connection Strings

```
Development (Local):   postgresql://postgres:password@localhost:5432/taxmate_ai
Docker Compose:        postgresql://postgres:password@db:5432/taxmate_ai
Production (AWS RDS):  postgresql://user:pass@my-db.us-east-1.rds.amazonaws.com:5432/taxmate_ai
With SSL:              postgresql://user:pass@host:5432/db?sslmode=require
```

---

## 📝 Common Commands

```bash
# List databases
psql -U postgres -h localhost -l

# Connect to database
psql -U postgres -h localhost -d taxmate_ai

# Reset database (DELETE ALL DATA)
psql -U postgres -h localhost -c "DROP DATABASE taxmate_ai;"
python setup_database.py

# Backup database
pg_dump -U postgres -h localhost -d taxmate_ai > backup.sql

# Restore from backup
psql -U postgres -h localhost -d taxmate_ai < backup.sql

# Check table row count
psql -U postgres -h localhost -d taxmate_ai -c "SELECT COUNT(*) FROM users;"
```

---

## 📞 Getting Help

1. Check: [DATABASE_SETUP.md](DATABASE_SETUP.md) for full documentation
2. Run setup script: `python setup_database.py` (has detailed error messages)
3. Check PostgreSQL logs: `docker-compose logs db`
4. Verify .env file is correct
5. Ensure PostgreSQL is running and accessible

---

**Status**: Ready for setup  
**Last Updated**: April 26, 2026
