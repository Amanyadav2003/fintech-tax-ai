import urllib.request, json

# Test login to port 5001 directly
login_payload = {"email":"Omkartri07@gmail.com","password":"Omkartri@123"}
login_data = json.dumps(login_payload).encode()
login_req = urllib.request.Request(
    "http://localhost:5001/api/auth/login",
    data=login_data,
    headers={"Content-Type":"application/json"},
    method="POST",
)

print("=== DIRECT BACKEND LOGIN TEST ===")
try:
    with urllib.request.urlopen(login_req, timeout=10) as resp:
        print('STATUS', resp.status)
        result = resp.read().decode()
        print('RESPONSE:', result)
        print('HEADERS:', dict(resp.headers))
except urllib.error.HTTPError as e:
    print('HTTPError', e.code)
    try:
        error_body = e.read().decode()
        print('ERROR BODY:', error_body)
    except Exception:
        pass
except Exception as e:
    print('ERROR', str(e))
