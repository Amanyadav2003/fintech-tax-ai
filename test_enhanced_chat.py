#!/usr/bin/env python3
"""
End-to-end test for Virtual Tax Professional System
Tests: Mode detection, Module routing, Response generation
Includes authentication flow
"""

import os
import requests
import json
from pprint import pprint
import sys
import time

BASE_URL = "http://localhost:5000/api"

# Test scenarios
test_cases = [
    {
        "name": "TRAINING Mode - Learn 80C",
        "query": "Teach me about Section 80C",
        "expected_mode": "training",
        "expected_module": "income_tax"
    },
    {
        "name": "EXECUTION Mode - Claim 80C",
        "query": "Help me claim Section 80C in my ITR",
        "expected_mode": "execution",
        "expected_module": "income_tax"
    },
    {
        "name": "HYBRID Mode - Explain and Calculate",
        "query": "Explain capital gains and help me calculate mine",
        "expected_mode": "hybrid",
        "expected_module": "income_tax"
    },
    {
        "name": "GST Module - Registration",
        "query": "Teach me how to register for GST",
        "expected_mode": "training",
        "expected_module": "gst"
    },
    {
        "name": "GST Execution - Register",
        "query": "Help me register for GST",
        "expected_mode": "execution",
        "expected_module": "gst"
    },
    {
        "name": "Accounting - Journal Entry",
        "query": "Teach me about journal entries",
        "expected_mode": "training",
        "expected_module": "accounting"
    },
]

def get_auth_token():
    """Register/Login and get JWT token"""
    
    print("\n[AUTH] Getting authentication token...")
    
    # Test credentials
    test_email = f"test_user_{int(time.time())}@example.com"
    test_password = os.getenv("CHAT_TEST_PASSWORD", "TestOnly-Chat-123!")
    
    try:
        # Try to register
        print(f"  Registering: {test_email}")
        register_response = requests.post(
            f"{BASE_URL}/auth/register",
            json={
                "email": test_email,
                "password": test_password,
                "full_name": "Test User"
            },
            timeout=5
        )
        
        if register_response.status_code == 200:
            print(f"  ✅ Registered successfully")
        elif register_response.status_code == 400:
            print(f"  ℹ️  User may already exist, attempting login")
        else:
            print(f"  ⚠️  Registration returned {register_response.status_code}")
        
        # Login to get token
        print(f"  Logging in...")
        login_response = requests.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": test_email,
                "password": test_password
            },
            timeout=5
        )
        
        if login_response.status_code != 200:
            print(f"  ❌ Login failed: HTTP {login_response.status_code}")
            print(f"  Response: {login_response.text}")
            return None
        
        data = login_response.json()
        token = data.get("access_token")
        
        if not token:
            print(f"  ❌ No token in response")
            return None
        
        print(f"  ✅ Token obtained")
        return token
        
    except Exception as e:
        print(f"  ❌ Auth error: {e}")
        return None

def test_chat_endpoint(token):
    """Test the chat endpoint with different scenarios"""
    
    print("\n" + "="*80)
    print("VIRTUAL TAX PROFESSIONAL - END-TO-END TEST")
    print("="*80)
    
    results = []
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n[Test {i}] {test['name']}")
        print(f"Query: {test['query']}")
        print("-" * 80)
        
        try:
            # Make request to chat endpoint with token
            response = requests.post(
                f"{BASE_URL}/tax/chat",
                json={
                    "message": test['query'],
                    "user_id": f"test_user_{i}"
                },
                headers={
                    "Authorization": f"Bearer {token}"
                },
                timeout=10
            )
            
            if response.status_code != 200:
                print(f"❌ Error: HTTP {response.status_code}")
                print(f"Response: {response.text}")
                results.append({
                    "test": test['name'],
                    "status": "FAILED",
                    "reason": f"HTTP {response.status_code}"
                })
                continue
            
            data = response.json()
            
            # Extract results
            mode = data.get("mode", "unknown")
            module = data.get("module", "unknown")
            response_text = data.get("response", "")[:150]  # First 150 chars
            next_steps = data.get("next_steps", [])
            
            # Validate
            mode_match = mode == test['expected_mode']
            module_match = module == test['expected_module']
            has_response = len(response_text) > 0
            has_next_steps = len(next_steps) > 0
            
            # Print results
            print(f"\nResults:")
            print(f"  Mode: {mode:15} {'✅' if mode_match else '❌ Expected: ' + test['expected_mode']}")
            print(f"  Module: {module:15} {'✅' if module_match else '❌ Expected: ' + test['expected_module']}")
            print(f"  Has Response: {has_response:15} {'✅' if has_response else '❌'}")
            print(f"  Has Next Steps: {has_next_steps:15} {'✅' if has_next_steps else '❌'}")
            
            if has_response:
                print(f"\nResponse Preview:")
                print(f"  {response_text}...")
            
            if has_next_steps:
                print(f"\nNext Steps:")
                for step in next_steps[:2]:
                    print(f"  • {step}")
            
            # Determine pass/fail
            all_pass = mode_match and module_match and has_response and has_next_steps
            status = "PASSED" if all_pass else "PARTIAL"
            
            results.append({
                "test": test['name'],
                "status": status,
                "mode_correct": mode_match,
                "module_correct": module_match,
                "has_response": has_response,
                "has_next_steps": has_next_steps
            })
            
            print(f"\nStatus: {status}")
            
        except requests.exceptions.ConnectionError as e:
            print(f"❌ Connection Error: {e}")
            results.append({
                "test": test['name'],
                "status": "FAILED",
                "reason": "Connection error - Backend may not be running"
            })
        except Exception as e:
            print(f"❌ Error: {e}")
            results.append({
                "test": test['name'],
                "status": "FAILED",
                "reason": str(e)
            })
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    passed = sum(1 for r in results if r["status"] == "PASSED")
    partial = sum(1 for r in results if r["status"] == "PARTIAL")
    failed = sum(1 for r in results if r["status"] == "FAILED")
    
    for result in results:
        status_icon = "✅" if result["status"] == "PASSED" else "⚠️" if result["status"] == "PARTIAL" else "❌"
        print(f"{status_icon} {result['test']:40} {result['status']}")
    
    print("\n" + "-"*80)
    print(f"Total: {len(results)} | Passed: {passed} | Partial: {partial} | Failed: {failed}")
    print("="*80)
    
    return passed == len(results)

if __name__ == "__main__":
    print("Starting Virtual Tax Professional E2E Tests...")
    
    # Try to read token from file first
    token = None
    try:
        with open("auth_token.txt", "r") as f:
            token = f.read().strip()
            print(f"✅ Token read from file")
    except FileNotFoundError:
        print("Token file not found, trying to authenticate...")
        token = get_auth_token()
    
    if not token:
        print("\n❌ Failed to get authentication token. Cannot proceed.")
        sys.exit(1)
    
    # Test chat with token
    success = test_chat_endpoint(token)
    sys.exit(0 if success else 1)
