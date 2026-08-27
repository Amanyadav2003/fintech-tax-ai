import urllib.request, urllib.parse, http.cookiejar, json

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

login_payload = {"email":"Omkartri07@gmail.com","password":"Omkartri@123"}
login_data = json.dumps(login_payload).encode()
login_req = urllib.request.Request(
    "http://localhost:5001/api/auth/login",
    data=login_data,
    headers={"Content-Type":"application/json"},
    method="POST",
)

try:
    with opener.open(login_req, timeout=10) as resp:
        print('LOGIN STATUS', resp.status)
        print(resp.read().decode())
except urllib.error.HTTPError as e:
    print('LOGIN HTTPError', e.code)
    try:
        print(e.read().decode())
    except Exception:
        pass
    raise SystemExit(1)

# Now call analyze
payload = {
    "income_data": {"salary": 1200000, "interest": 5000, "dividend": 2000},
    "deductions_data": {"section80c": 150000, "home_loan_interest": 50000}
}

analyze_data = json.dumps(payload).encode()
_analyze_req = urllib.request.Request(
    "http://localhost:5001/api/tax/analyze",
    data=analyze_data,
    headers={"Content-Type": "application/json"},
    method="POST",
)

try:
    with opener.open(_analyze_req, timeout=10) as resp:
        print('ANALYZE STATUS', resp.status)
        print(resp.read().decode())
except urllib.error.HTTPError as e:
    print('ANALYZE HTTPError', e.code)
    try:
        print(e.read().decode())
    except Exception:
        pass
except Exception as e:
    print('ANALYZE ERROR', str(e))
