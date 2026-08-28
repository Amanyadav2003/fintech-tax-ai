import os
import sqlite3

db_path = "backend/taxmate_ai.db"

try:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    target_email = os.getenv("TEST_CHECK_EMAIL", "final-user@example.invalid")
    cursor.execute("""
        SELECT id, email, name, phone, pan, is_active, created_at
        FROM users 
        WHERE email = ?
    """, (target_email,))
    
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
        print(f"❌ User '{target_email}' not found!")
    
    conn.close()
    
except Exception as e:
    print(f"ERROR: {e}")
