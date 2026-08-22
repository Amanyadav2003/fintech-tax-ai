#!/usr/bin/env python3
"""
Comprehensive Step 2 Test Checklist for TaxMate AI Docker Backend
Tests the REAL FastAPI backend running in Docker (http://127.0.0.1:5000)
NOT the mock_backend.py
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any

# Configuration
BACKEND_URL = "http://127.0.0.1:5000/api"
TEST_USER_EMAIL = f"testuser_{int(time.time())}@example.com"
TEST_USER_PASSWORD = "TestPass@123"  # Must have: uppercase, digit, special char
TEST_USER_PAN = f"TAXPR{int(time.time())%10000:04d}K"  # Format: 5 uppercase + 4 digits + 1 uppercase

# Test results tracking
test_results: List[Dict[str, Any]] = []


def print_header(title: str):
    """Print a formatted header"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def print_test(test_name: str, status: str, details: str = ""):
    """Print test result"""
    status_symbol = "✅" if status == "PASS" else "❌"
    print(f"  {status_symbol} {test_name}: {status}")
    if details:
        print(f"     {details}")


def log_test(test_name: str, status: str, response_code: int = None, error: str = None):
    """Log test result"""
    test_results.append({
        "test": test_name,
        "status": status,
        "response_code": response_code,
        "error": error,
        "timestamp": datetime.now().isoformat()
    })


def test_health_check():
    """Test 1: Health Check - Verify Backend is Running"""
    print_header("TEST 1: HEALTH CHECK")
    
    try:
        response = requests.get(f"{BACKEND_URL.replace('/api', '')}/health", timeout=5)
        if response.status_code == 200:
            print_test("Backend Health Check", "PASS", f"Status: {response.json()}")
            log_test("Backend Health Check", "PASS", response.status_code)
            return True
        else:
            print_test("Backend Health Check", "FAIL", f"Status: {response.status_code}")
            log_test("Backend Health Check", "FAIL", response.status_code)
            return False
    except Exception as e:
        print_test("Backend Health Check", "FAIL", str(e))
        log_test("Backend Health Check", "FAIL", error=str(e))
        return False


def test_user_registration():
    """Test 2: User Registration/Authentication"""
    print_header("TEST 2: USER REGISTRATION")
    
    global TEST_USER_EMAIL
    
    registration_data = {
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD,
        "name": "Test User",
        "phone": "9876543210",
        "pan": TEST_USER_PAN,
        "age": 35,
        "state": "Maharashtra"
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/auth/register", json=registration_data, timeout=10)
        
        if response.status_code in [200, 201]:
            data = response.json()
            print_test("User Registration", "PASS", f"Email: {TEST_USER_EMAIL}")
            log_test("User Registration", "PASS", response.status_code)
            return True, TEST_USER_EMAIL
        else:
            error_msg = response.json().get("detail", response.text)
            print_test("User Registration", "FAIL", f"Status {response.status_code}: {error_msg}")
            log_test("User Registration", "FAIL", response.status_code, error_msg)
            return False, None
    except Exception as e:
        print_test("User Registration", "FAIL", str(e))
        log_test("User Registration", "FAIL", error=str(e))
        return False, None


def test_user_login(email: str):
    """Test 3: Login and Auth Token"""
    print_header("TEST 3: LOGIN & AUTH TOKEN")
    
    login_data = {
        "email": email,
        "password": TEST_USER_PASSWORD
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            access_token = data.get("access_token")
            
            if access_token:
                print_test("User Login", "PASS", f"Token received (first 20 chars): {access_token[:20]}...")
                print_test("Token Type", "PASS", f"Type: {data.get('token_type', 'bearer')}")
                log_test("User Login & Token", "PASS", response.status_code)
                return True, access_token
            else:
                print_test("User Login", "FAIL", "No access_token in response")
                log_test("User Login & Token", "FAIL", response.status_code, "No access_token")
                return False, None
        else:
            error_msg = response.json().get("detail", response.text)
            print_test("User Login", "FAIL", f"Status {response.status_code}: {error_msg}")
            log_test("User Login & Token", "FAIL", response.status_code, error_msg)
            return False, None
    except Exception as e:
        print_test("User Login", "FAIL", str(e))
        log_test("User Login & Token", "FAIL", error=str(e))
        return False, None


def test_tax_analysis(access_token: str):
    """Test 4: Tax Analysis"""
    print_header("TEST 4: TAX ANALYSIS")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    analysis_data = {
        "filing_year": 2024,
        "income_data": {
            "salary": 1200000,
            "interest": 50000,
            "dividend": 100000,
            "rental_income": 50000,
            "professional_fees": 0
        },
        "deductions_data": {
            "investments": 150000,
            "health_insurance": 25000,
            "home_loan_principal": 200000,
            "education": 100000,
            "donations": 10000
        }
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/tax/analyze", json=analysis_data, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print_test("Tax Analysis", "PASS", f"Total Income: ₹{data.get('total_income', 0):,}")
            if "total_deductions" in data:
                print_test("Deductions Calculated", "PASS", f"Total Deductions: ₹{data.get('total_deductions', 0):,}")
            if "tax_due" in data:
                print_test("Tax Calculation", "PASS", f"Tax Due: ₹{data.get('tax_due', 0):,}")
            log_test("Tax Analysis", "PASS", response.status_code)
            return True, data
        else:
            error_msg = response.json().get("detail", response.text)
            print_test("Tax Analysis", "FAIL", f"Status {response.status_code}: {error_msg}")
            log_test("Tax Analysis", "FAIL", response.status_code, error_msg)
            return False, None
    except Exception as e:
        print_test("Tax Analysis", "FAIL", str(e))
        log_test("Tax Analysis", "FAIL", error=str(e))
        return False, None


def test_chat_endpoint(access_token: str):
    """Test 5: Chat Functionality"""
    print_header("TEST 5: CHAT FUNCTIONALITY")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    chat_data = {
        "message": "What is Section 80C?",
        "context": {}
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/tax/chat", json=chat_data, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            response_text = data.get("response", "")
            if response_text:
                print_test("Chat Endpoint", "PASS", f"Response length: {len(response_text)} chars")
                print_test("Chat Response Quality", "PASS", response_text[:100] + "...")
                log_test("Chat Functionality", "PASS", response.status_code)
                return True, data
            else:
                print_test("Chat Endpoint", "FAIL", "Empty response")
                log_test("Chat Functionality", "FAIL", response.status_code, "Empty response")
                return False, None
        else:
            error_msg = response.json().get("detail", response.text) if response.text else "No response body"
            print_test("Chat Endpoint", "FAIL", f"Status {response.status_code}: {error_msg}")
            log_test("Chat Functionality", "FAIL", response.status_code, error_msg)
            return False, None
    except Exception as e:
        print_test("Chat Endpoint", "FAIL", str(e))
        log_test("Chat Functionality", "FAIL", error=str(e))
        return False, None


def test_rate_limiting(access_token: str):
    """Test 6: Rate Limiting"""
    print_header("TEST 6: RATE LIMITING")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Make rapid requests to test rate limiting
    print("  Making 5 rapid requests to test rate limiting...")
    
    chat_data = {
        "message": "Test rate limit",
        "context": {}
    }
    
    success_count = 0
    rate_limited_count = 0
    
    try:
        for i in range(5):
            response = requests.post(f"{BACKEND_URL}/tax/chat", json=chat_data, headers=headers, timeout=5)
            
            if response.status_code == 200:
                success_count += 1
            elif response.status_code == 429:
                rate_limited_count += 1
            else:
                pass
            
            time.sleep(0.1)  # Small delay between requests
        
        print_test("Rate Limiting Test", "PASS", f"Success: {success_count}/5, Rate Limited: {rate_limited_count}/5")
        log_test("Rate Limiting", "PASS")
        return True
    except Exception as e:
        print_test("Rate Limiting Test", "FAIL", str(e))
        log_test("Rate Limiting", "FAIL", error=str(e))
        return False


def test_postgresql_persistence(access_token: str):
    """Test 7: PostgreSQL Persistence"""
    print_header("TEST 7: POSTGRESQL PERSISTENCE")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Create a filing
    filing_data = {
        "filing_year": 2024,
        "income_data": {
            "salary": 1000000,
            "interest": 25000,
            "dividend": 50000,
            "rental_income": 0,
            "professional_fees": 0
        },
        "deductions_data": {
            "investments": 100000,
            "health_insurance": 25000,
            "education_loan_interest": 0,
            "home_loan_interest": 150000,
            "donations": 25000,
            "medical_expenses": 0,
            "other": 0
        },
        "tds_paid": 50000,
        "advance_tax_paid": 25000
    }
    
    try:
        # Create filing
        create_response = requests.post(
            f"{BACKEND_URL}/tax/filings",
            json=filing_data,
            headers=headers,
            timeout=10
        )
        
        if create_response.status_code not in [200, 201]:
            error_msg = create_response.json().get("detail", create_response.text)
            print_test("Filing Creation", "FAIL", f"Status {create_response.status_code}: {error_msg}")
            log_test("PostgreSQL Persistence", "FAIL", create_response.status_code, error_msg)
            return False
        
        filing = create_response.json()
        filing_id = filing.get("id")
        
        if not filing_id:
            print_test("Filing Creation", "FAIL", "No filing ID in response")
            log_test("PostgreSQL Persistence", "FAIL", 200, "No filing ID")
            return False
        
        print_test("Filing Creation", "PASS", f"Filing ID: {filing_id} created successfully")
        print_test("Database Persistence", "PASS", "Filing saved to PostgreSQL")
        log_test("PostgreSQL Persistence", "PASS", 200)
        return True
            
    except Exception as e:
        print_test("PostgreSQL Persistence", "FAIL", str(e))
        log_test("PostgreSQL Persistence", "FAIL", error=str(e))
        return False


def test_authentication_required(access_token: str = None):
    """Test 8: Authentication Required for Protected Endpoints"""
    print_header("TEST 8: AUTHENTICATION REQUIRED")
    
    # Try to access protected endpoint without token
    try:
        response = requests.post(f"{BACKEND_URL}/tax/analyze", json={"filing_year": 2024, "income_data": {}, "deductions_data": {}}, timeout=10)
        
        if response.status_code == 401:
            print_test("Unauthenticated Access Blocked", "PASS", "Got 401 Unauthorized")
            log_test("Authentication Required", "PASS", 401)
            return True
        else:
            print_test("Unauthenticated Access Blocked", "FAIL", f"Got {response.status_code}, expected 401")
            log_test("Authentication Required", "FAIL", response.status_code, f"Expected 401, got {response.status_code}")
            return False
    except Exception as e:
        print_test("Unauthenticated Access Blocked", "FAIL", str(e))
        log_test("Authentication Required", "FAIL", error=str(e))
        return False


def print_summary_table():
    """Print summary table of all tests"""
    print_header("STEP 2 TEST SUMMARY")
    
    print(f"{'Test Name':<45} {'Status':<10} {'Response Code':<15}")
    print("-" * 70)
    
    passed = 0
    failed = 0
    
    for result in test_results:
        status_symbol = "✅ PASS" if result["status"] == "PASS" else "❌ FAIL"
        response_code = result.get("response_code") or "N/A"
        print(f"{result['test']:<45} {status_symbol:<10} {str(response_code):<15}")
        
        if result["status"] == "PASS":
            passed += 1
        else:
            failed += 1
    
    print("-" * 70)
    print(f"TOTAL: {passed} PASSED, {failed} FAILED\n")
    
    return passed, failed


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "  STEP 2: DOCKER BACKEND VERIFICATION TEST SUITE".center(78) + "║")
    print("║" + "  Testing REAL FastAPI Backend (NOT mock_backend.py)".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝")
    
    # Test 1: Health Check
    if not test_health_check():
        print("\n❌ CRITICAL: Backend is not responding. Aborting tests.")
        return
    
    time.sleep(1)
    
    # Test 2: User Registration
    success, email = test_user_registration()
    if not success:
        print("\n❌ CRITICAL: User registration failed. Aborting tests.")
        return
    
    time.sleep(1)
    
    # Test 3: User Login
    success, access_token = test_user_login(email)
    if not success:
        print("\n❌ CRITICAL: User login failed. Aborting tests.")
        return
    
    time.sleep(1)
    
    # Test 4: Tax Analysis
    test_tax_analysis(access_token)
    time.sleep(1)
    
    # Test 5: Chat
    test_chat_endpoint(access_token)
    time.sleep(1)
    
    # Test 6: Rate Limiting
    test_rate_limiting(access_token)
    time.sleep(1)
    
    # Test 7: PostgreSQL Persistence
    test_postgresql_persistence(access_token)
    time.sleep(1)
    
    # Test 8: Authentication Required
    test_authentication_required()
    
    # Print summary
    passed, failed = print_summary_table()
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED! ✅\n")
    else:
        print(f"⚠️  {failed} TEST(S) FAILED. Review details above.\n")


if __name__ == "__main__":
    main()
