#!/usr/bin/env python3
"""
Register a test user and get a token for testing
"""

import requests
import json
import os
import sys

BASE_URL = "http://localhost:5000/api"

# Use a simpler email
test_email = os.getenv("TEST_AUTH_EMAIL", "auth-user@example.invalid")
test_password = os.getenv("TEST_AUTH_PASSWORD", "TestOnly-Auth-123!")

print("Attempting to register test user...")

try:
    # Register
    register_response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": test_email,
            "password": test_password,
            "full_name": "Test User",
            "name": "Test User",
            "phone": "9999999999",
            "pan": "AAAPA9999A",
            "age": 30,
            "state": "Delhi"
        },
        timeout=5
    )
    
    print(f"Register response: {register_response.status_code}")
    print(f"Response body: {register_response.text}")
    
    # Try to login
    print("\nAttempting to login...")
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": test_email,
            "password": test_password
        },
        timeout=5
    )
    
    print(f"Login response: {login_response.status_code}")
    print(f"Response body: {login_response.text}")
    
    if login_response.status_code == 200:
        data = login_response.json()
        token = data.get("access_token")
        print(f"\n✅ Token obtained: {token[:50]}...")
        
        # Save token to file for other tests
        with open("auth_token.txt", "w") as f:
            f.write(token)
        print("Token saved to auth_token.txt")

except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
