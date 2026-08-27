import urllib.request, json, http.cookiejar

# Test different passwords for final@test.com
test_passwords = [
    "FinalUser@123",
    "Final@123",
    "password",
    "test",
    "123456",
]

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

print("Testing login attempts for final@test.com")
print("=" * 60)

for password in test_passwords:
    payload = {"email": "final@test.com", "password": password}
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
print("Email: Omkartri07@gmail.com")
print("Password: Omkartri@123")
