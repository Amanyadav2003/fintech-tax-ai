import requests
import json

# Register a new test user
register_url = "http://localhost:5000/api/auth/register"
register_data = {
    "email": "tokentest@example.com",
    "password": "TokenTest@123",
    "name": "Token Tester",
    "phone": "9876543210",
    "pan": "TOKNT1234T",
    "age": 30,
    "state": "Maharashtra"
}

print("1. Registering new user...")
reg_response = requests.post(register_url, json=register_data)
print(f"   Status: {reg_response.status_code}")
if reg_response.status_code != 200:
    print(f"   Error: {reg_response.json()}")
else:
    print("   ✓ Registration successful")

# Now test login with the new user
login_url = "http://localhost:5000/api/auth/login"
login_data = {
    "email": "tokentest@example.com",
    "password": "TokenTest@123"
}

print("\n2. Testing login with new user...")
login_response = requests.post(login_url, json=login_data)
print(f"   Status: {login_response.status_code}")
print(f"   Response keys: {list(login_response.json().keys())}")

if login_response.status_code == 200:
    response_data = login_response.json()
    token = response_data.get("access_token")
    
    if token:
        print(f"   ✓ Access token received: {token[:30]}...")
        print(f"   ✓ Token type: {response_data.get('token_type')}")
        print(f"   ✓ Expires in: {response_data.get('expires_in')} seconds")
        
        # Test tax endpoint with token
        print("\n3. Testing tax analysis endpoint with token...")
        tax_url = "http://localhost:5000/api/tax/analyze"
        headers = {"Authorization": f"Bearer {token}"}
        tax_data = {
            "filing_year": 2024,
            "income_data": {
                "salary": 500000,
                "interest": 10000,
                "dividend": 5000,
                "rental_income": 20000,
                "professional_fees": 0
            },
            "deductions_data": {
                "investments": 150000,
                "health_insurance": 25000,
                "home_loan_principal": 50000,
                "education": 100000,
                "donations": 10000
            }
        }
        
        tax_response = requests.post(tax_url, json=tax_data, headers=headers)
        print(f"   Status: {tax_response.status_code}")
        
        if tax_response.status_code == 200:
            print("   ✓ Tax analysis successful!")
            result = tax_response.json()
            print(f"   Response has keys: {list(result.keys())}")
        else:
            print(f"   ✗ Tax endpoint error: {tax_response.json()}")
    else:
        print("   ✗ No access_token in response")
        print(f"   Full response: {json.dumps(response_data, indent=2)}")
else:
    print(f"   ✗ Login failed: {login_response.json()}")
