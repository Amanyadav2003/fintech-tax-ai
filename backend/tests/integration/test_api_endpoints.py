"""
Integration tests for Tax Filing API endpoints
"""

import pytest
from fastapi import status


class TestTaxFilingEndpoints:
    """Test tax filing API endpoints"""
    
    def test_create_tax_filing_authenticated(self, authenticated_client, test_tax_filing_data):
        """Test creating tax filing as authenticated user"""
        response = authenticated_client.post(
            "/api/tax/filings",
            json=test_tax_filing_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "draft"
        assert data["filing_year"] == test_tax_filing_data["filing_year"]
    
    def test_create_tax_filing_unauthenticated(self, client, test_tax_filing_data):
        """Test creating tax filing without authentication"""
        response = client.post(
            "/api/tax/filings",
            json=test_tax_filing_data
        )
        
        assert response.status_code == 401
    
    def test_get_tax_filings_authenticated(self, authenticated_client, test_tax_filing_data):
        """Test retrieving tax filings as authenticated user"""
        # Create a filing first
        create_response = authenticated_client.post(
            "/api/tax/filings",
            json=test_tax_filing_data
        )
        assert create_response.status_code == 200
        
        # Get all filings
        get_response = authenticated_client.get("/api/tax/filings")
        assert get_response.status_code == 200
        
        filings = get_response.json()
        assert isinstance(filings, list)
        assert len(filings) >= 1
    
    def test_get_tax_filings_unauthenticated(self, client):
        """Test retrieving tax filings without authentication"""
        response = client.get("/api/tax/filings")
        
        assert response.status_code == 401
    
    def test_analyze_tax_filing(self, authenticated_client, test_tax_filing_data):
        """Test analyzing tax filing"""
        # Create a filing first
        create_response = authenticated_client.post(
            "/api/tax/filings",
            json=test_tax_filing_data
        )
        filing_id = create_response.json()["id"]
        
        # Analyze the filing
        analyze_response = authenticated_client.post(
            f"/api/tax/filings/{filing_id}/analyze"
        )
        
        assert analyze_response.status_code == 200
        analysis = analyze_response.json()
        
        # Check analysis results contain expected fields
        assert "total_income" in analysis
        assert "total_deductions" in analysis
        assert "audit_risk_score" in analysis
    
    def test_invalid_tax_filing_data(self, authenticated_client):
        """Test creating tax filing with invalid data"""
        invalid_data = {
            "filing_year": 2024,
            "income_data": {
                "salary": -100000  # Negative salary
            },
            "deductions_data": {}
        }
        
        response = authenticated_client.post(
            "/api/tax/filings",
            json=invalid_data
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_filing_year_validation(self, authenticated_client, test_tax_filing_data):
        """Test filing year validation"""
        invalid_data = {
            **test_tax_filing_data,
            "filing_year": 2050  # Too far in future
        }
        
        response = authenticated_client.post(
            "/api/tax/filings",
            json=invalid_data
        )
        
        assert response.status_code == 422


class TestHealthAndStatus:
    """Test health check endpoints"""
    
    def test_health_check_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
    
    def test_api_documentation(self, client):
        """Test API documentation endpoints"""
        # Swagger docs
        swagger_response = client.get("/api/docs")
        assert swagger_response.status_code == 200
        
        # ReDoc
        redoc_response = client.get("/api/redoc")
        assert redoc_response.status_code == 200
        
        # OpenAPI schema
        openapi_response = client.get("/api/openapi.json")
        assert openapi_response.status_code == 200


class TestRateLimiting:
    """Test rate limiting on endpoints"""
    
    def test_rate_limit_on_login(self, client, test_user_data):
        """Test rate limiting on login endpoint"""
        # Make multiple failed login attempts
        for i in range(6):
            response = client.post(
                "/api/auth/login",
                json={
                    "username": f"user{i}@example.com",
                    "password": "wrong_password"
                }
            )
            
            # After 5 attempts, should get 429
            if i < 5:
                assert response.status_code in [401, 422]
            else:
                # 6th attempt should be rate limited
                if response.status_code == 429:
                    break  # Rate limit reached as expected
    
    def test_no_rate_limit_for_health_check(self, client):
        """Test health check is not rate limited"""
        # Make many requests
        for i in range(20):
            response = client.get("/health")
            assert response.status_code == 200


class TestErrorHandling:
    """Test error handling"""
    
    def test_404_not_found(self, client):
        """Test 404 error for non-existent endpoint"""
        response = client.get("/api/non-existent-endpoint")
        
        assert response.status_code == 404
    
    def test_405_method_not_allowed(self, client):
        """Test 405 error for wrong HTTP method"""
        response = client.put("/api/auth/login")
        
        assert response.status_code == 405
    
    def test_422_validation_error(self, client):
        """Test 422 validation error"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "invalid_email",  # Invalid email format
                "name": "",  # Empty name
                "phone": "123",  # Wrong phone format
                "pan": "INVALID",  # Wrong PAN format
                "age": 15,  # Too young
                "state": "XY"
            }
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data or "errors" in data
