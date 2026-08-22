import sqlite3

db_path = "backend/taxmate_ai.db"

try:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Check final@test.com user
    cursor.execute("""
        SELECT id, email, name, phone, pan, is_active, created_at
        FROM users 
        WHERE email = 'final@test.com'
    """)
    
    user = cursor.fetchone()
    if user:
        print("✅ User found in database:")
        print(f"   ID: {user['id']}")
        print(f"   Email: {user['email']}")
        print(f"   Name: {user['name']}")
        print(f"   Phone: {user['phone']}")
        print(f"   PAN: {user['pan']}")
        print(f"   Active: {user['is_active']}")
        print(f"   Created: {user['created_at']}")
        print("\n⚠️  The user exists, but the password might not match what you entered.")
        print("\nLet me test login with a known working user instead...")
    else:
        print("❌ User 'final@test.com' not found!")
    
    conn.close()
    
except Exception as e:
    print(f"ERROR: {e}")
