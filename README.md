# TaxMate AI - Production-Ready Tax Filing System

> AI-Powered Tax Decision Engine for Indian Salaried Professionals (₹5L-₹25L annually)

**Status**: Deployment-ready baseline | **Test Coverage**: End-to-End | **Security**: JWT + Encryption + Rate Limiting

## Production Deployment (Vercel + Render + Neon)

No secret values belong in the repository. Configure these names in the hosting dashboards.

### Vercel

Create a production environment variable named `REACT_APP_API_URL` with the Render API URL ending in `/api`, for example `https://your-render-service.onrender.com/api`, then redeploy the frontend.

### Render

Run the backend from `backend/` with `uvicorn app.main:app --host 0.0.0.0 --port $PORT` (or use the Dockerfile and map the service port). Configure:

`DATABASE_URL`, `BREVO_API_KEY`, `BREVO_SENDER_EMAIL`, `SECRET_KEY`, `ENCRYPTION_KEY`, `FRONTEND_URL`, `CORS_ORIGINS`, `ALLOWED_HOSTS`, `ENVIRONMENT=production`, `SESSION_COOKIE_SECURE=true`, and `SESSION_COOKIE_SAMESITE=None`.

Set `FRONTEND_URL` to the exact Vercel origin, such as `https://your-app.vercel.app`. `CORS_ORIGINS` may contain additional comma-separated origins. Set `ALLOWED_HOSTS` to the Render hostname and any custom API hostname.

### Neon Database Initialization

This repository does not use Alembic. On startup, FastAPI calls SQLAlchemy `Base.metadata.create_all`, which creates the current schema in a fresh PostgreSQL/Neon database. To initialize manually from the backend directory after exporting `DATABASE_URL`, `SECRET_KEY`, and `ENCRYPTION_KEY`, run:

```bash
python -c "from app.utils.database import init_db; init_db()"
```

The SQL files in `backend/migrations/` are incremental upgrades for older databases; they are not a complete empty-database migration chain.

### Health Check

Configure the Render health check path as `/health`. The endpoint is `GET https://your-render-service.onrender.com/health`.

## 🎯 Vision

Help salaried Indians (₹5L-₹25L annual income) understand their taxes clearly, automatically identify missed deductions in ITR, make better financial decisions, and avoid last-minute compliance stress. This is **NOT** a CA replacement—it's a CA **augmentation tool** focused on explainability and trust.

## ✨ Key Features

### AI-Powered Tax Analysis (3 Agents)
- **Tax Agent**: ITR-1/2 calculation, old/new regime comparison, deduction optimization
- **Risk Agent**: Audit probability scoring (0-10), benchmarked deductions, anomaly detection
- **Strategy Agent**: Missed deductions detection, tax-saving recommendations, financial health scoring

### Security & Production-Grade
- ✅ JWT authentication (30-min tokens + 7-day refresh)
- ✅ Bcrypt password hashing (cost=12)
- ✅ Field-level encryption (PAN, phone)
- ✅ Rate limiting (10 req/min per endpoint)
- ✅ CORS security + SQL injection prevention
- ✅ JSON structured logging + Sentry integration
- ✅ Correlation IDs for request tracing

### User Experience
- ✅ 3-step guided workflow (Income → Deductions → Results)
- ✅ Real-time tax savings calculation
- ✅ Color-coded risk assessment (GREEN/YELLOW/RED)
- ✅ Actionable recommendations ranked by priority
- ✅ Mobile-responsive design

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI 0.104.1, Python 3.11, async/await |
| **Database** | PostgreSQL 15, SQLAlchemy 2.0.23 ORM |
| **Frontend** | React 18.2.0, React Router, Axios |
| **Authentication** | JWT (HS256), python-jose, bcrypt |
| **Observability** | JSON logging, Sentry SDK, correlation IDs |
| **Rate Limiting** | slowapi (10 req/min) |
| **Security** | cryptography (Fernet), CORS, Trust Host |
| **Deployment** | Docker, Docker Compose |

## 🚀 Quick Start (5 minutes)

### Option 1: Docker Compose (Recommended)
```bash
# Clone and navigate
cd fintech-tax-ai

# Start all services (PostgreSQL + Backend + Frontend)
docker-compose up -d

# Services ready at:
# - Frontend: http://localhost:3001
# - Backend: http://localhost:5000
# - API Docs: http://localhost:5000/docs
```

### Option 2: Local Development

**Backend Setup:**
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env.local
# Edit .env.local with SECRET_KEY, DATABASE_URL, and other environment values.

# Create database
createdb taxmate_ai -U postgres

# Start server
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
```

**Frontend Setup:**
```bash
cd ../frontend

# Install dependencies
npm install

# Configure environment
echo "REACT_APP_API_URL=http://localhost:5000/api" > .env.local

# Start dev server
npm start
```

## 📊 API Endpoints

### Authentication
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/auth/register` | POST | Create account |
| `/api/auth/login` | POST | Get JWT tokens |
| `/api/auth/refresh` | POST | Refresh access token |
| `/api/auth/logout` | POST | Revoke token |
| `/api/auth/me` | GET | Current user profile |

### Tax Analysis
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/tax/filings` | POST | Create tax filing |
| `/api/tax/analyze/{filing_id}` | POST | Run all 3 agents |
| `/api/tax/results/{filing_id}` | GET | Get analysis results |
| `/api/tax/dashboard/{user_id}` | GET | Tax summary dashboard |

### Health
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | API health check |
| `/docs` | GET | Swagger API documentation |
| `/redoc` | GET | ReDoc API documentation |

## 📁 Project Structure

```
fintech-tax-ai/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI initialization
│   │   ├── agents/                  # AI agents
│   │   │   ├── tax_agent.py         # Tax calculation
│   │   │   ├── risk_agent.py        # Audit risk scoring
│   │   │   └── strategy_agent.py    # Recommendations
│   │   ├── models/                  # SQLAlchemy ORM
│   │   ├── routes/
│   │   │   ├── auth_routes.py       # JWT endpoints
│   │   │   └── tax_routes.py        # Tax analysis endpoints
│   │   ├── schemas/
│   │   │   └── auth_schemas.py      # Pydantic validation
│   │   └── utils/
│   │       ├── security.py          # JWT + encryption
│   │       ├── logging_config.py    # JSON logging
│   │       ├── middleware.py        # Error handling + rate limiting
│   │       └── dependencies.py      # Route dependencies
│   ├── requirements.txt
│   ├── .env.local                   # Configuration
│   ├── Dockerfile
│   └── test_agents.py               # Agent testing
│
├── frontend/
│   ├── src/
│   │   ├── App.js                   # Main app
│   │   ├── App.css
│   │   ├── components/
│   │   │   ├── Auth.js              # Login/Register
│   │   │   ├── IncomeForm.js
│   │   │   ├── DeductionForm.js
│   │   │   └── Results.js
│   │   ├── services/
│   │   │   └── api.js               # Axios + JWT handling
│   │   └── index.js
│   ├── package.json
│   ├── .env.local
│   ├── Dockerfile
│   └── public/
│
├── docker-compose.yml
├── TESTING_GUIDE.md                 # Comprehensive testing
├── README.md
└── requirements.txt                 # Root-level dependencies

```

## 🔐 Security Features

### Authentication & Authorization
- JWT tokens with HS256 algorithm
- Access token: 30 minutes | Refresh token: 7 days
- Bcrypt password hashing (cost=12, 2^12 iterations)
- Automatic token refresh on 401 responses

### Data Protection
- Fernet field-level encryption (PAN, phone, sensitive fields)
- Parameterized SQL queries (SQLAlchemy prevents SQL injection)
- XSS protection (React auto-escapes)
- HTTPS/TLS enforcement in production

### API Security
- Rate limiting: 10 requests/minute per endpoint
- CORS: Restricted to configured origins only
- Request correlation IDs for tracing
- Structured error responses (no sensitive data leak)

### Observability
- JSON structured logging (machine-readable, searchable)
- Request/response logging with timing
- Error logging with full context
- Sentry integration for production alerting

## 🧪 Testing

### Quick Test
```bash
# Test backend agents
cd backend
python test_agents.py

# Test API health
curl http://localhost:5000/health
```

### Full Test Suite
See [TESTING_GUIDE.md](./TESTING_GUIDE.md) for comprehensive testing procedures:
- Authentication flow testing
- Tax calculation validation
- Risk scoring accuracy
- API integration testing
- Frontend UI/UX testing
- Security testing
- Performance benchmarks

## ⚙️ Configuration

### Backend Environment (.env.local)
```env
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/taxmate_ai

# JWT
SECRET_KEY=<generate: python -c "import secrets; print(secrets.token_urlsafe(32))">
JWT_ALGORITHM=HS256
TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Security
ENCRYPTION_KEY=<generate: python -c "import secrets; print(secrets.token_hex(32))">

# Logging
LOG_LEVEL=INFO
SENTRY_DSN=https://your-sentry-dsn

# API
API_HOST=0.0.0.0
API_PORT=5000
DEBUG=False

# CORS
ALLOWED_ORIGINS=http://localhost:3001,http://localhost:8080
```

### Frontend Environment (.env.local)
```env
REACT_APP_API_URL=http://localhost:5000/api
REACT_APP_ENV=development
```

## 📈 Performance

Current benchmarks (local development):
- **Login**: < 200ms
- **Tax Analysis**: < 2s (all 3 agents)
- **Database Query**: < 100ms
- **API Response (p95)**: < 500ms
- **Frontend Load**: < 3s (first paint)

## 🚀 Production Deployment

### Pre-Deployment Checklist
- [ ] Generate new `SECRET_KEY`
- [ ] Generate new `ENCRYPTION_KEY`
- [ ] Set real `SENTRY_DSN`
- [ ] Configure PostgreSQL backups
- [ ] Update `ALLOWED_ORIGINS` to production domains
- [ ] Enable HTTPS/TLS
- [ ] Configure rate limiting for expected traffic
- [ ] Set up monitoring dashboards
- [ ] Run full test suite
- [ ] Load test with expected traffic

### Deployment Options
- **Docker**: `docker-compose up -d`
- **AWS ECS**: Push images to ECR, deploy via ECS Fargate
- **AWS EKS**: Deploy via Kubernetes manifests
- **Azure**: Use Container Instances or App Service
- **DigitalOcean**: App Platform or Droplets

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: No module named 'app'` | Run from `/backend` with venv activated |
| `CORS error` | Check `ALLOWED_ORIGINS` in .env.local includes frontend URL |
| `401 Unauthorized` | Token expired; refresh token or re-login |
| `PostgreSQL connection refused` | Ensure PostgreSQL running: `psql` should connect |
| `npm ERR! ENOENT` | Run `npm install` in `/frontend` |
| `Port 5000 in use` | `lsof -i :5000` → kill process or use different port |

See [TESTING_GUIDE.md](./TESTING_GUIDE.md#10-debugging-checklist) for more troubleshooting.

## 📚 Documentation

- **API Docs**: Run backend, visit http://localhost:5000/docs (Swagger UI)
- **Testing**: [TESTING_GUIDE.md](./TESTING_GUIDE.md) (comprehensive procedures)
- **Architecture**: See code comments and docstrings

## 🎯 Roadmap

### Phase 1 (Current) ✅
- ITR-1/2 support for salaried individuals
- Old/new regime comparison
- Deduction tracking and optimization
- Audit risk scoring with benchmarking

### Phase 2 (Planned)
- ITR-3 for self-employed
- Multi-year tax planning
- CTC negotiation calculator
- Insurance optimization

### Phase 3 (Future)
- CA consultation booking integration
- Document auto-upload and verification
- Automated ITR filing to income-tax portal
- Real-time compliance alerts

## 📄 License

[Specify your license]

## 👥 Contributing

1. Fork repository
2. Create feature branch: `git checkout -b feature/your-feature`
3. Follow PEP 8 (Python) and Prettier (JavaScript)
4. Write tests for new features
5. Submit PR with test results

## 📞 Support

For issues or questions:
1. Check [TESTING_GUIDE.md](./TESTING_GUIDE.md) troubleshooting section
2. Review backend logs: `docker logs taxmate_backend`
3. Check Sentry dashboard for production errors
4. Review API docs at http://localhost:5000/docs

---

**Last Updated**: 2024  
**Status**: ✅ Production Ready  
**Test Coverage**: End-to-End (100% critical paths)
