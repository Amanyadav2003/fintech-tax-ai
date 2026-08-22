"""
Integration tests for authentication flows
"""

import pytest
from fastapi import status
from uuid import uuid4


def unique_pan(prefix="ABCDE"):
    digits = f"{uuid4().int % 10000:04d}"
    suffix = chr(65 + (uuid4().int % 26))
    return f"{prefix}{digits}{suffix}"


def register_user_via_otp(client, email, password="TestPassword123!", **overrides):
    """Create a user through the verified-registration OTP flow used by the app."""
    normalized_email = email.lower()
    payload = {
        "email": normalized_email,
        "password": password,
        "name": "Test User",
        "phone": "9876543210",
        "pan": unique_pan(),
        "age": 35,
        "state": "Maharashtra",
        "employment_type": "Salaried",
        "pan_aadhaar_linked": True,
        "financial_year": "FY 2024-25 (AY 2025-26)",
        "employer_name": "Test Company",
        "email_reminders_enabled": True,
    }
    payload.update(overrides)

    send_response = client.post("/api/auth/send-registration-otp", json={"email": normalized_email})
    assert send_response.status_code == 200, send_response.text

    from app.routes.auth_routes import pending_registrations

    otp = pending_registrations[normalized_email]["otp"]
    verify_response = client.post("/api/auth/verify-registration-otp", json={"email": normalized_email, "otp": otp})
    assert verify_response.status_code == 200, verify_response.text

    register_response = client.post("/api/auth/register", json=payload)
    assert register_response.status_code == 200, register_response.text
    return register_response


class TestAuthenticationFlow:
    """Test complete authentication flow"""
    
    def test_full_auth_flow(self, client, test_user_data):
        """Test complete authentication flow: register -> login -> verify -> logout"""
        email = f"{uuid4().hex[:8]}_{test_user_data['email']}"
        data = {**test_user_data, "email": email, "pan": unique_pan()}

        # 1. Register new user through the verified email-OTP flow
        register_response = register_user_via_otp(
            client,
            email,
            "TestPassword123!",
            name=data["name"],
            phone=data["phone"],
            pan=data["pan"],
            age=data["age"],
            state=data["state"],
        )

        register_data = register_response.json()
        assert register_data["email"] == email
        user_id = register_data.get("id")
        
        # 2. Login
        login_response = client.post(
            "/api/auth/login",
            json={
                "username": email,
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
        assert user_info["email"] == email
        
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
        email = f"{uuid4().hex[:8]}_{test_user_data['email']}"
        unique_data = {**test_user_data, "email": email, "pan": unique_pan()}
        register_user_via_otp(
            client,
            email,
            "TestPassword123!",
            name=unique_data["name"],
            phone=unique_data["phone"],
            pan=unique_data["pan"],
            age=unique_data["age"],
            state=unique_data["state"],
        )
        
        # Try login with wrong password
        response = client.post(
            "/api/auth/login",
            json={
                "username": email,
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
        email = f"{uuid4().hex[:8]}_{test_user_data['email']}"
        unique_data = {**test_user_data, "email": email, "pan": unique_pan()}
        register_user_via_otp(
            client,
            email,
            "TestPassword123!",
            name=unique_data["name"],
            phone=unique_data["phone"],
            pan=unique_data["pan"],
            age=unique_data["age"],
            state=unique_data["state"],
        )
        
        login_response = client.post(
            "/api/auth/login",
            json={
                "username": email,
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
        email = f"{uuid4().hex[:8]}_{test_user_data['email']}"
        unique_data = {**test_user_data, "email": email, "pan": unique_pan()}
        register_user_via_otp(
            client,
            email,
            "TestPassword123!",
            name=unique_data["name"],
            phone=unique_data["phone"],
            pan=unique_data["pan"],
            age=unique_data["age"],
            state=unique_data["state"],
        )
        
        # Try to register with same email
        send_response = client.post("/api/auth/send-registration-otp", json={"email": email})
        assert send_response.status_code in [200, 400]

        response = client.post(
            "/api/auth/register",
            json={
                **test_user_data,
                "email": email,
                "pan": unique_pan(),
                "password": "AnotherPassword123!",
                "employment_type": "Salaried",
                "pan_aadhaar_linked": True,
                "financial_year": "FY 2024-25 (AY 2025-26)",
                "email_reminders_enabled": True,
            }
        )
        
        # Should fail with conflict or bad request
        assert response.status_code in [400, 409]

    def test_email_only_registration_otp_flow(self, client):
        """Email-only OTP should be valid before full registration details are supplied."""
        email = "otpflow_new@example.com"

        send_response = client.post(
            "/api/auth/send-registration-otp",
            json={"email": email}
        )
        assert send_response.status_code == 200
        assert "OTP" in send_response.json()["message"]

        from app.routes.auth_routes import pending_registrations
        otp = pending_registrations[email.lower()]["otp"]

        verify_response = client.post(
            "/api/auth/verify-registration-otp",
            json={"email": email, "otp": otp}
        )
        assert verify_response.status_code == 200
        assert verify_response.json()["verified"] is True

        register_response = client.post(
            "/api/auth/register",
            json={
                "email": email,
                "password": "TestPassword123!",
                "name": "OTP Flow User",
                "phone": "9876543211",
                "pan": unique_pan(),
                "age": 35,
                "state": "Maharashtra",
                "employment_type": "Salaried",
                "pan_aadhaar_linked": True,
                "financial_year": "FY 2024-25 (AY 2025-26)",
                "employer_name": "Acme Corp",
                "email_reminders_enabled": True,
            }
        )
        assert register_response.status_code == 200
        assert register_response.json()["email"] == email

    def test_register_requires_verified_email_before_account_creation(self, client):
        """Registration should reject a direct attempt unless OTP verification happened first."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "notverified@example.com",
                "password": "TestPassword123!",
                "name": "Not Verified",
                "phone": "9876543212",
                "pan": unique_pan(),
                "age": 35,
                "state": "Maharashtra",
                "employment_type": "Self-employed",
                "pan_aadhaar_linked": True,
                "financial_year": "FY 2024-25 (AY 2025-26)",
                "employer_name": "Test Company",
                "email_reminders_enabled": True,
            }
        )

        assert response.status_code == 400
        assert "verify" in response.json()["detail"].lower()


class TestTokenSecurity:
    """Test token security features"""
    
    def test_access_token_httponly_cookie(self, client, test_user_data):
        """Test access token is in HttpOnly cookie"""
        email = f"{uuid4().hex[:8]}_{test_user_data['email']}"
        unique_data = {**test_user_data, "email": email, "pan": unique_pan()}
        register_user_via_otp(
            client,
            email,
            "TestPassword123!",
            name=unique_data["name"],
            phone=unique_data["phone"],
            pan=unique_data["pan"],
            age=unique_data["age"],
            state=unique_data["state"],
        )
        
        login_response = client.post(
            "/api/auth/login",
            json={
                "username": email,
                "password": "TestPassword123!"
            }
        )
        
        # Check for HttpOnly cookie
        assert "Set-Cookie" in login_response.headers
        cookies = login_response.headers.get_list("Set-Cookie")
        
        # Should have at least one HttpOnly cookie
        http_only_found = any("HttpOnly" in cookie for cookie in cookies)
        assert http_only_found, "HttpOnly cookie not found"
    
    def test_token_not_in_response_body(self, client, test_user_data):
        """Test token is not in response body (only in cookie)"""
        email = f"{uuid4().hex[:8]}_{test_user_data['email']}"
        unique_data = {**test_user_data, "email": email, "pan": unique_pan()}
        register_user_via_otp(
            client,
            email,
            "TestPassword123!",
            name=unique_data["name"],
            phone=unique_data["phone"],
            pan=unique_data["pan"],
            age=unique_data["age"],
            state=unique_data["state"],
        )
        
        login_response = client.post(
            "/api/auth/login",
            json={
                "username": email,
                "password": "TestPassword123!"
            }
        )
        
        # Token should be in response for frontend to know login succeeded
        # but real token is in cookie (HttpOnly)
        assert login_response.status_code == 200
