import os
import urllib.request, json, http.cookiejar

# Test different passwords for a configured test identity.
test_passwords = os.getenv("TEST_PASSWORD_CANDIDATES", "TestOnly-Final-123!,TestOnly-Alternate-123!,password,test,123456").split(",")
test_email = os.getenv("TEST_FINAL_EMAIL", "final-user@example.invalid")

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

print(f"Testing login attempts for {test_email}")
print("=" * 60)

for password in test_passwords:
    payload = {"email": test_email, "password": password}
    data = json.dumps(payload).encode()
    
    req = urllib.request.Request(
        "http://localhost:5001/api/auth/login",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    
    try:
        with opener.open(req, timeout=10) as resp:
            print(f"✅ Password '{password}': SUCCESS (200)")
            result = resp.read().decode()
            print(f"   Response: {result[:100]}...")
            break  # Found the right password
    except urllib.error.HTTPError as e:
        if e.code == 401:
            print(f"❌ Password '{password}': FAILED (401 Unauthorized)")
        else:
            print(f"⚠️  Password '{password}': ERROR ({e.code})")
    except Exception as e:
        print(f"⚠️  Password '{password}': ERROR - {str(e)[:50]}")

print("\n" + "=" * 60)
print("If none work, try the test user instead:")
print(f"Email: {test_email}")
print("Passwords: supplied through TEST_PASSWORD_CANDIDATES")
