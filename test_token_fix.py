import requests
import json

# Test login with the fix
url = "http://127.0.0.1:5000/api/auth/login"
data = {
    "email": "testuser123@example.com",
    "password": "Test@12345"
}

response = requests.post(url, json=data)
print(f"Status Code: {response.status_code}")
print(f"Response:\n{json.dumps(response.json(), indent=2)}")

# If we got the token, try the tax endpoint
if response.status_code == 200:
    token = response.json().get("access_token")
    if token:
        print(f"\n✓ Access token received: {token[:20]}...")
        
        # Test tax endpoint with token
        tax_url = "http://127.0.0.1:5000/api/tax/analyze"
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
        print(f"\nTax endpoint status: {tax_response.status_code}")
        if tax_response.status_code == 200:
            print("✓ Tax analysis successful!")
            print(f"Response: {json.dumps(tax_response.json(), indent=2)[:200]}...")
        else:
            print(f"Tax endpoint error: {tax_response.text}")
    else:
        print("✗ No access_token in response")
