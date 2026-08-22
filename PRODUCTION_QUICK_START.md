# Production Deployment Quick Start Guide

## Prerequisites

- Docker and Docker Compose installed
- SSL/TLS certificate (from Let's Encrypt or your provider)
- Domain name (e.g., yourdomain.com)
- Generated production keys (SECRET_KEY, ENCRYPTION_KEY)

## Step 1: Prepare Environment

```bash
# Copy production env template
cp backend/.env.production .env.production

# Edit with production values
nano .env.production

# Required changes:
# - DB_PASSWORD: Change to strong password
# - SECRET_KEY: Already generated
# - ENCRYPTION_KEY: Already generated
# - CORS_ORIGINS: Set to your domain
# - ALLOWED_HOSTS: Set to your domain
# - REACT_APP_API_URL: Set to https://api.yourdomain.com
```

## Step 2: Generate Database

```bash
# Create initial database (if not using automated setup)
docker-compose -f docker-compose.prod.yml --env-file .env.production up -d db

# Wait for database to be ready
sleep 10

# Initialize database schema
docker-compose -f docker-compose.prod.yml --env-file .env.production \
  exec backend python setup_database.py
```

## Step 3: Deploy with Docker Compose

```bash
# Pull latest images
docker pull postgres:15-alpine
docker pull python:3.11-slim
docker pull node:18-alpine

# Build and start all services
docker-compose -f docker-compose.prod.yml --env-file .env.production up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f backend
```

## Step 4: Verify Services

```bash
# Test backend health
curl http://localhost:5000/health

# Test frontend
curl http://localhost:3000

# Check database connection
docker-compose -f docker-compose.prod.yml \
  exec db psql -U postgres -d taxmate_ai -c "SELECT COUNT(*) FROM users;"
```

## Step 5: Setup SSL/TLS (HTTPS)

### Option A: Using Let's Encrypt with Certbot

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot certonly --standalone -d yourdomain.com -d api.yourdomain.com

# Certificates will be in: /etc/letsencrypt/live/yourdomain.com/
# - fullchain.pem
# - privkey.pem

# Copy to your server
mkdir -p ./certs
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ./certs/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ./certs/
sudo chown $USER:$USER ./certs/*
```

### Option B: Using AWS Certificate Manager (if on AWS)

```bash
# Use AWS ACM to generate certificate
# Then configure your load balancer to terminate SSL
```

## Step 6: Setup Nginx Reverse Proxy (Optional but Recommended)

```bash
# Copy Nginx configuration
cp nginx.conf.template nginx/nginx.conf

# Edit for your domain
nano nginx/nginx.conf

# Uncomment nginx service in docker-compose.prod.yml

# Restart with Nginx
docker-compose -f docker-compose.prod.yml --env-file .env.production restart
```

## Step 7: Setup Automated Backups

```bash
# Make backup script executable
chmod +x backend/backup_database.sh

# Add to crontab for daily backups at 2 AM
(crontab -l 2>/dev/null; echo "0 2 * * * /path/to/backend/backup_database.sh >> /var/log/db_backup.log 2>&1") | crontab -

# Test backup script
bash backend/backup_database.sh
```

## Step 8: Setup Monitoring

```bash
# Install monitoring stack (optional)
docker run -d -p 9090:9090 \
  -v ./prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus

docker run -d -p 3001:3000 \
  -e GF_SECURITY_ADMIN_PASSWORD=admin \
  grafana/grafana
```

## Step 9: Run Smoke Tests

```bash
# Create test user
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "name": "Test User",
    "phone": "9876543210",
    "pan": "ABCDE1234F",
    "age": 35,
    "state": "Maharashtra",
    "password": "TestPassword123!"
  }'

# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{
    "username": "test@example.com",
    "password": "TestPassword123!"
  }'

# Create tax filing
curl -X POST http://localhost:5000/api/tax/filings \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "filing_year": 2024,
    "income_data": {"salary": 1000000},
    "deductions_data": {"investments": 150000}
  }'
```

## Step 10: Monitor and Maintain

```bash
# Check container logs
docker-compose -f docker-compose.prod.yml logs -f backend

# Monitor resource usage
docker stats

# Check disk space
df -h

# Verify backups exist
ls -lh /backups/postgresql/backup_*.sql.gz

# Test backup recovery
bash backend/restore_database.sh /backups/postgresql/backup_taxmate_ai_YYYYMMDD_HHMMSS.sql.gz
```

## Troubleshooting

### Database connection issues
```bash
docker-compose -f docker-compose.prod.yml logs db
docker-compose -f docker-compose.prod.yml exec db pg_isready -U postgres
```

### Backend not starting
```bash
docker-compose -f docker-compose.prod.yml logs backend
docker-compose -f docker-compose.prod.yml exec backend python -c "from app.main import app; print('App loaded')"
```

### Frontend not accessible
```bash
docker-compose -f docker-compose.prod.yml logs frontend
docker-compose -f docker-compose.prod.yml exec frontend wget -O - http://localhost:3000/
```

### SSL certificate issues
```bash
# Check certificate
openssl x509 -in ./certs/fullchain.pem -text -noout

# Renew certificate
sudo certbot renew --force-renewal
```

## Backup and Recovery

### Manual backup
```bash
bash backend/backup_database.sh
```

### Manual recovery
```bash
bash backend/restore_database.sh /path/to/backup.sql.gz
```

### Automated recovery from S3 (if configured)
```bash
aws s3 cp s3://your-bucket/backups/backup_taxmate_ai_*.sql.gz ./
bash backend/restore_database.sh ./backup_taxmate_ai_*.sql.gz
```

## Performance Tuning

### Database optimization
- Monitor slow queries: `docker-compose exec db psql -U postgres -d taxmate_ai -c "SHOW log_statement;"`
- Analyze query plans: `EXPLAIN ANALYZE SELECT ...;`
- Add indexes if needed: `CREATE INDEX idx_name ON table(column);`

### Backend optimization
- Increase workers: Set `WORKERS=8` in .env for 4+ CPU
- Enable caching: Add Redis service and update code
- Monitor response times: Check Prometheus metrics

### Frontend optimization
- Enable gzip compression in Nginx
- Setup CDN for static assets
- Enable browser caching headers

## Scaling for Production

### Vertical scaling (more resources)
```yaml
# In docker-compose.prod.yml
deploy:
  resources:
    limits:
      cpus: '4'      # Increase from 2
      memory: 4G     # Increase from 2G
```

### Horizontal scaling (multiple instances)
```bash
# Create multiple backend instances
docker-compose -f docker-compose.prod.yml up -d --scale backend=3
```

### Load balancing
```bash
# Use Nginx upstream to load balance
# See nginx/nginx.conf for upstream configuration
```

---

**Important**: Always backup before making production changes!
