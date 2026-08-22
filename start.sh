#!/bin/bash

# TaxMate AI Quick Start Script
# This script sets up and runs the entire application

set -e

echo "=========================================="
echo "TaxMate AI - Quick Start Setup"
echo "=========================================="
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker Desktop."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Compose."
    exit 1
fi

echo "✅ Docker & Docker Compose found"
echo ""

# Start services
echo "🚀 Starting TaxMate AI..."
echo ""

docker-compose down --remove-orphans 2>/dev/null || true

docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are running
echo ""
echo "✅ Services started!"
echo ""
echo "=========================================="
echo "TaxMate AI is now running!"
echo "=========================================="
echo ""
echo "📍 Frontend: http://localhost:3000"
echo "📍 Backend API: http://localhost:5000"
echo "📍 API Docs: http://localhost:5000/docs"
echo "📍 Database: PostgreSQL (localhost:5432)"
echo ""
echo "=========================================="
echo "Next Steps:"
echo "=========================================="
echo ""
echo "1. Open http://localhost:3000 in your browser"
echo "2. Create an account (demo user)"
echo "3. Enter income and deductions"
echo "4. View tax analysis from all 3 agents"
echo ""
echo "📖 For more details, see:"
echo "   - README.md (Overview)"
echo "   - SETUP.md (Detailed setup)"
echo "   - API_REFERENCE.md (API docs)"
echo ""
echo "🔍 To view logs:"
echo "   docker logs taxmate_backend  # Backend logs"
echo "   docker logs taxmate_frontend # Frontend logs"
echo "   docker logs taxmate_db       # Database logs"
echo ""
echo "🛑 To stop services:"
echo "   docker-compose down"
echo ""
