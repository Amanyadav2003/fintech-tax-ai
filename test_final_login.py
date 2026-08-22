import urllib.request, json

payload = {"email": "final@test.com", "password": "Final@123"}
data = json.dumps(payload).encode()

req = urllib.request.Request(
    "http://127.0.0.1:5001/api/auth/login",
    data=data,
    headers={"Content-Type": "application/json"},
    method="POST",
)

try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        print(f"✅ LOGIN SUCCESS (Status {resp.status})")
        result = json.loads(resp.read().decode())
        print(f"Message: {result['message']}")
        print(f"User: {result['user']['name']} ({result['user']['email']})")
except urllib.error.HTTPError as e:
    print(f"❌ Login failed: {e.code}")
    try:
        print(json.loads(e.read().decode()))
    except:
        pass
except Exception as e:
    print(f"ERROR: {e}")
