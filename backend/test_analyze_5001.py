import urllib.request, json

payload = {
    "income_data": {"salary": 1200000, "interest": 5000, "dividend": 2000},
    "deductions_data": {"section80c": 150000, "home_loan_interest": 50000}
}

data = json.dumps(payload).encode()
req = urllib.request.Request(
    "http://localhost:5001/api/tax/analyze",
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
