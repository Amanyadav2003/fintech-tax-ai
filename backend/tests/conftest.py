"""
Pytest configuration and fixtures for the test suite
"""

import pytest
import os
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient


TEST_SQLITE_URL = "sqlite://"

# Set test environment
os.environ['ENVIRONMENT'] = 'test'
os.environ['DEBUG'] = 'false'
os.environ['SECRET_KEY'] = 'test-secret-key-12345678901234567890123456789012'
os.environ['ENCRYPTION_KEY'] = 'KHIO0Y6qNXe576O8de8wh0wNQo5N_zMqG_0ZODfwriU='


@pytest.fixture(scope="session")
def test_db():
    """Create a single shared SQLite in-memory database for the whole test session."""
    engine = create_engine(
        TEST_SQLITE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Bind the app's database module to the same engine so startup/init_db and tests use the same connection pool.
    import app.utils.database as database_module
    database_module.engine = engine
    database_module.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    from app.models import Base
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture
def db_session(test_db):
    """Create a fresh database session for each test against the shared SQLite connection."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db)
    db = TestingSessionLocal()
    yield db
    db.rollback()
    db.close()


@pytest.fixture
def client(db_session):
    """Create a test client with a per-request database session override and a shared SQLite engine."""
    from app.main import app
    from app.utils.database import get_db
    from app.routes import auth_routes

    auth_routes.pending_registrations.clear()
    auth_routes.resend_attempts.clear()

    if hasattr(app.state, "limiter"):
        try:
            app.state.limiter.reset()
        except Exception:
            pass

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    """Sample user data for tests"""
    return {
        "email": "test@example.com",
        "name": "Test User",
        "phone": "9876543210",
        "pan": "ABCDE1234F",
        "age": 35,
        "state": "Maharashtra"
    }


@pytest.fixture
def test_tax_filing_data():
    """Sample tax filing data for tests"""
    return {
        "filing_year": 2024,
        "income_data": {
            "salary": 1200000,
            "interest": 50000,
            "dividend": 100000,
            "rental_income": 0,
            "professional_fees": 0
        },
        "deductions_data": {
            "investments": 150000,
            "health_insurance": 25000,
            "education_loan_interest": 0,
            "home_loan_interest": 200000,
            "donations": 50000,
            "medical_expenses": 0,
            "other": 0
        },
        "tds_paid": 150000,
        "advance_tax_paid": 100000
    }


@pytest.fixture
def authenticated_client(client, test_user_data):
    """Create an authenticated test client"""
    from app.routes.auth_routes import pending_registrations
    test_user_data = {
        **test_user_data,
        "email": f"{uuid4().hex[:8]}_{test_user_data['email']}",
        "pan": f"ABCDE{uuid4().int % 10000:04d}F",
    }

    # Registration requires the same verified-email setup as the production flow.
    send_response = client.post(
        "/api/auth/send-registration-otp",
        json={"email": test_user_data["email"]}
    )
    assert send_response.status_code == 200
    otp = pending_registrations[test_user_data["email"]]["otp"]
    verify_response = client.post(
        "/api/auth/verify-registration-otp",
        json={"email": test_user_data["email"], "otp": otp}
    )
    assert verify_response.status_code == 200

    # Register user
    register_response = client.post(
        "/api/auth/register",
        json={
            **test_user_data,
            "password": "TestPassword123!"
        }
    )
    
    assert register_response.status_code == 200
    
    # Login
    login_response = client.post(
        "/api/auth/login",
        json={
            "username": test_user_data["email"],
            "password": "TestPassword123!"
        }
    )
    
    assert login_response.status_code == 200
    
    # Cookies are automatically handled by TestClient
    return client
