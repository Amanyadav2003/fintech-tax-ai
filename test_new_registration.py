import urllib.request, json

# Test registration with a new user
new_user = {
    "name": "Test Register",
    "email": "testregister@gmail.com",
    "password": "TestPass@123",
    "phone": "9876543210",
    "pan": "XYZZZ1234D",
    "age": 30,
    "state": "MH"
}

data = json.dumps(new_user).encode()
req = urllib.request.Request(
    "http://localhost:5000/api/auth/register",
    data=data,
    headers={"Content-Type":"application/json"},
    method="POST",
)

print("=== TESTING NEW USER REGISTRATION ===")
print(f"Payload: {json.dumps(new_user, indent=2)}")
print("\n=== REQUEST ===")

try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        print(f'STATUS: {resp.status} OK')
        result = resp.read().decode()
        print(f'RESPONSE:\n{json.dumps(json.loads(result), indent=2)}')
except urllib.error.HTTPError as e:
    print(f'HTTPError {e.code}')
    try:
        error = json.loads(e.read().decode())
        print(f'ERROR RESPONSE:\n{json.dumps(error, indent=2)}')
    except:
        print(e.read().decode())
except Exception as e:
    print(f'ERROR: {str(e)}')
