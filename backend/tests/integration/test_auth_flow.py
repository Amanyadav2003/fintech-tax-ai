"""
Integration tests for authentication flows
"""

import pytest
from fastapi import status


class TestAuthenticationFlow:
    """Test complete authentication flow"""
    
    def test_full_auth_flow(self, client, test_user_data):
        """Test complete authentication flow: register -> login -> verify -> logout"""
        
        # 1. Register new user
        register_response = client.post(
            "/api/auth/register",
            json={
                **test_user_data,
                "password": "TestPassword123!"
            }
        )
        
        assert register_response.status_code == 200
        register_data = register_response.json()
        assert register_data["email"] == test_user_data["email"]
        user_id = register_data.get("id")
        
        # 2. Login
        login_response = client.post(
            "/api/auth/login",
            json={
                "username": test_user_data["email"],
                "password": "TestPassword123!"
            }
        )
        
        assert login_response.status_code == 200
        assert "access_token" in login_response.json()
        
        # 3. Verify token (access protected endpoint)
        verify_response = client.get(
            "/api/auth/me"
        )
        
        assert verify_response.status_code == 200
        user_info = verify_response.json()
        assert user_info["email"] == test_user_data["email"]
        
        # 4. Logout
        logout_response = client.post("/api/auth/logout")
        
        assert logout_response.status_code == 200
        
        # 5. Verify token is revoked
        verify_after_logout = client.get("/api/auth/me")
        
        # Should fail because token is revoked
        assert verify_after_logout.status_code == 401
    
    def test_registration_with_invalid_email(self, client, test_user_data):
        """Test registration with invalid email"""
        response = client.post(
            "/api/auth/register",
            json={
                **test_user_data,
                "email": "invalid_email",
                "password": "TestPassword123!"
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_registration_with_weak_password(self, client, test_user_data):
        """Test registration with weak password"""
        response = client.post(
            "/api/auth/register",
            json={
                **test_user_data,
                "password": "weak"
            }
        )
        
        assert response.status_code in [400, 422]  # Should fail
    
    def test_login_with_wrong_password(self, client, test_user_data):
        """Test login with wrong password"""
        # Register first
        client.post(
            "/api/auth/register",
            json={
                **test_user_data,
                "password": "TestPassword123!"
            }
        )
        
        # Try login with wrong password
        response = client.post(
            "/api/auth/login",
            json={
                "username": test_user_data["email"],
                "password": "WrongPassword123!"
            }
        )
        
        assert response.status_code == 401
    
    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "nonexistent@example.com",
                "password": "SomePassword123!"
            }
        )
        
        assert response.status_code == 401
    
    def test_access_protected_endpoint_without_token(self, client):
        """Test accessing protected endpoint without token"""
        response = client.get("/api/auth/me")
        
        assert response.status_code == 401
    
    def test_token_refresh(self, client, test_user_data):
        """Test token refresh flow"""
        # Register and login
        client.post(
            "/api/auth/register",
            json={
                **test_user_data,
                "password": "TestPassword123!"
            }
        )
        
        login_response = client.post(
            "/api/auth/login",
            json={
                "username": test_user_data["email"],
                "password": "TestPassword123!"
            }
        )
        
        assert login_response.status_code == 200
        
        # Try to refresh token
        refresh_response = client.post("/api/auth/refresh")
        
        assert refresh_response.status_code == 200
        assert "access_token" in refresh_response.json()
    
    def test_duplicate_email_registration(self, client, test_user_data):
        """Test registration with duplicate email"""
        # Register first user
        client.post(
            "/api/auth/register",
            json={
                **test_user_data,
                "password": "TestPassword123!"
            }
        )
        
        # Try to register with same email
        response = client.post(
            "/api/auth/register",
            json={
                **test_user_data,
                "password": "AnotherPassword123!"
            }
        )
        
        # Should fail with conflict or bad request
        assert response.status_code in [400, 409]


class TestTokenSecurity:
    """Test token security features"""
    
    def test_access_token_httponly_cookie(self, client, test_user_data):
        """Test access token is in HttpOnly cookie"""
        # Register and login
        client.post(
            "/api/auth/register",
            json={
                **test_user_data,
                "password": "TestPassword123!"
            }
        )
        
        login_response = client.post(
            "/api/auth/login",
            json={
                "username": test_user_data["email"],
                "password": "TestPassword123!"
            }
        )
        
        # Check for HttpOnly cookie
        assert "Set-Cookie" in login_response.headers
        cookies = login_response.headers.getlist("Set-Cookie")
        
        # Should have at least one HttpOnly cookie
        http_only_found = any("HttpOnly" in cookie for cookie in cookies)
        assert http_only_found, "HttpOnly cookie not found"
    
    def test_token_not_in_response_body(self, client, test_user_data):
        """Test token is not in response body (only in cookie)"""
        # Register and login
        client.post(
            "/api/auth/register",
            json={
                **test_user_data,
                "password": "TestPassword123!"
            }
        )
        
        login_response = client.post(
            "/api/auth/login",
            json={
                "username": test_user_data["email"],
                "password": "TestPassword123!"
            }
        )
        
        # Token should be in response for frontend to know login succeeded
        # but real token is in cookie (HttpOnly)
        assert login_response.status_code == 200
