import os
import urllib.request, json

data = json.dumps({
    "name": "Omkar",
    "email": os.getenv("TEST_REGISTER_EMAIL", "register-user@example.invalid"),
    "password": os.getenv("TEST_REGISTER_PASSWORD", "TestOnly-Register-123!"),
    "phone": "7045575020",
    "pan": "ASDFG4562A",
    "age": 25,
    "state": "MH"
}).encode()

req = urllib.request.Request(
    "http://localhost:5000/api/auth/register",
    data=data,
    headers={"Content-Type": "application/json"},
    method="POST",
)

try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        print("STATUS", resp.status)
        print(resp.read().decode())
except urllib.error.HTTPError as e:
    print("HTTPError", e.code)
    try:
        print(e.read().decode())
    except Exception:
        pass
except Exception as e:
    print("ERROR", str(e))
