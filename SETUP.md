# TaxMate AI - Deployment & Setup Guide

## Quick Start with Docker (Recommended)

### Prerequisites
- Docker & Docker Compose installed
- Git

### Start the Application

```bash
# Clone and navigate
git clone <repo>
cd fintech-tax-ai

# Start all services
docker-compose up

# Wait for services to initialize (~30 seconds)
```

Services will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **API Docs (Swagger)**: http://localhost:5000/docs
- **Database**: PostgreSQL on localhost:5432

---

## Local Development Setup

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your PostgreSQL URL

# Initialize database
alembic upgrade head

# Run tests
python test_agents.py

# Start server
uvicorn app.main:app --reload
# Server runs on http://localhost:5000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
# Opens http://localhost:3000
```

---

## Project Structure

```
fintech-tax-ai/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── tax_agent.py      # Tax calculation engine
│   │   │   ├── risk_agent.py     # Audit risk detection
│   │   │   └── strategy_agent.py # Financial planning
│   │   ├── models/               # Database models
│   │   ├── routes/               # API endpoints
│   │   ├── schemas/              # Pydantic validators
│   │   ├── utils/                # Helpers
│   │   └── main.py               # FastAPI app
│   ├── requirements.txt
│   ├── Dockerfile
│   └── test_agents.py
│
├── frontend/
│   ├── src/
│   │   ├── components/           # React components
│   │   ├── services/             # API clients
│   │   ├── styles/               # CSS files
│   │   ├── App.js
│   │   └── index.js
│   ├── package.json
│   ├── Dockerfile
│   └── public/
│
├── docker-compose.yml
└── README.md
```

---

## API Endpoints

### Users
- `POST /api/users` - Register new user
- `GET /api/users/{user_id}` - Get user profile

### Tax Filing
- `POST /api/tax-filing` - Create tax filing
- `POST /api/analyze/{filing_id}` - Run analysis (all 3 agents)
- `GET /api/results/{filing_id}` - Get analysis results
- `GET /api/dashboard/{user_id}` - Get user dashboard

### Interactive API Docs
- Visit: http://localhost:5000/docs (Swagger UI)
- Or: http://localhost:5000/redoc (ReDoc)

---

## Testing

### Test Agents Locally
```bash
cd backend
python test_agents.py
```

This runs a complete workflow through all 3 agents with sample data.

### Manual API Testing
```bash
# Create a user
curl -X POST http://localhost:5000/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "name": "Test User",
    "phone": "9876543210",
    "pan": "AAAPA1234A",
    "age": 35,
    "state": "Maharashtra"
  }'

# Create tax filing
curl -X POST http://localhost:5000/api/tax-filing \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "filing_year": 2024,
    "income_data": {
      "salary": 1200000,
      "interest": 50000,
      "dividend": 0,
      "rental_income": 0,
      "professional_fees": 0
    },
    "deductions_data": {
      "investments": 150000,
      "health_insurance": 25000,
      "education_loan_interest": 0,
      "home_loan_interest": 0,
      "donations": 0
    }
  }'

# Analyze filing
curl -X POST http://localhost:5000/api/analyze/1 \
  -H "Content-Type: application/json"
```

---

## Database Management

### Reset Database (Docker)
```bash
docker-compose down -v
docker-compose up
```

### Access PostgreSQL Directly
```bash
# Inside container
docker exec -it taxmate_db psql -U postgres -d taxmate_ai

# Common commands
\dt                    # List tables
SELECT * FROM users;   # Query users
\q                     # Exit
```

---

## Deployment

### Docker Build
```bash
# Build images
docker-compose build

# Push to registry
docker tag fintech-tax-ai-backend:latest your-registry/taxmate-backend:v1
docker push your-registry/taxmate-backend:v1
```

### Production Deployment (AWS/Azure/GCP)
1. Set up RDS/Cloud SQL for PostgreSQL
2. Update DATABASE_URL in environment
3. Deploy backend to App Engine/ECS/Container Apps
4. Deploy frontend to S3/Blob Storage + CloudFront/CDN
5. Set CORS origins in backend environment

---

## Environment Variables

### Backend (.env)
```
DATABASE_URL=postgresql://user:pass@host:5432/taxmate_ai
API_HOST=0.0.0.0
API_PORT=5000
DEBUG=False
CORS_ORIGINS=http://localhost:3000
```

### Frontend (.env.local)
```
REACT_APP_API_URL=http://localhost:5000/api
REACT_APP_ENV=development
```

---

## Troubleshooting

### Port Already in Use
```bash
# Find process using port
lsof -i :5000  # Backend
lsof -i :3000  # Frontend

# Kill process
kill -9 <PID>
```

### Database Connection Error
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Check logs
docker logs taxmate_db
```

### CORS Issues
- Ensure CORS_ORIGINS in backend includes frontend URL
- Restart backend after changing environment

### Frontend Can't Reach Backend
- Verify backend is running: http://localhost:5000/health
- Check REACT_APP_API_URL in frontend .env
- Check browser console for error details

---

## Performance Optimization

### Backend
- Use connection pooling (SQLAlchemy)
- Add caching for benchmark data
- Consider async agents for I/O

### Frontend
- Code splitting with React.lazy()
- Image optimization
- Use production build: `npm run build`

---

## Security Checklist

- [ ] Change default database password
- [ ] Enable HTTPS in production
- [ ] Set secure CORS origins
- [ ] Use environment variables for secrets
- [ ] Implement authentication/JWT
- [ ] Add rate limiting to API
- [ ] Encrypt sensitive user data (PAN, etc.)
- [ ] Regular security audits

---

## Support & Contribution

For issues or improvements:
1. Create GitHub issue with details
2. Submit pull request for fixes
3. Follow code style guidelines

---

## License

MIT - See LICENSE file for details
