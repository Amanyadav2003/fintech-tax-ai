import urllib.request, json, http.cookiejar

# Test what the frontend would see
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# Simulate frontend login request
login_payload = {"email":"Omkartri07@gmail.com","password":"Omkartri@123"}
login_data = json.dumps(login_payload).encode()

# Frontend would call this (with Origin header)
login_req = urllib.request.Request(
    "http://localhost:5001/api/auth/login",
    data=login_data,
    headers={
        "Content-Type":"application/json",
        "Origin": "http://localhost:3001"
    },
    method="POST",
)

print("=== SIMULATING FRONTEND LOGIN ===")
try:
    with opener.open(login_req, timeout=10) as resp:
        print(f'STATUS: {resp.status}')
        body = resp.read().decode()
        print(f'RESPONSE: {body}')
        print(f'COOKIES: {[str(c) for c in cj]}')
        
        # Check if we can use the cookie for follow-up request
        analyze_payload = {"income_data": {"salary": 1000000}, "deductions_data": {"section80c": 100000}}
        analyze_data = json.dumps(analyze_payload).encode()
        analyze_req = urllib.request.Request(
            "http://localhost:5001/api/tax/analyze",
            data=analyze_data,
            headers={"Content-Type":"application/json"},
            method="POST"
        )
        
        print("\n=== FOLLOW-UP ANALYZE REQUEST ===")
        with opener.open(analyze_req, timeout=10) as resp2:
            print(f'ANALYZE STATUS: {resp2.status}')
            print(f'ANALYZE RESPONSE: {resp2.read().decode()[:200]}...')
except urllib.error.HTTPError as e:
    print(f'HTTPError {e.code}')
    try:
        print(e.read().decode())
    except:
        pass
except Exception as e:
    print(f'ERROR: {str(e)}')
