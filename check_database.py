import sqlite3

db_path = "backend/taxmate_ai.db"

try:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Check if users table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if cursor.fetchone():
        print("=== USERS TABLE EXISTS ===")
        cursor.execute("SELECT COUNT(*) as count FROM users")
        count = cursor.fetchone()['count']
        print(f"Total users: {count}")
        
        print("\n=== USER RECORDS ===")
        cursor.execute("SELECT id, email, name, phone, pan, is_active, created_at FROM users")
        for row in cursor.fetchall():
            print(f"ID: {row['id']}, Email: {row['email']}, Name: {row['name']}, Phone: {row['phone']}, PAN: {row['pan']}, Active: {row['is_active']}, Created: {row['created_at']}")
    else:
        print("ERROR: Users table does not exist!")
    
    conn.close()
except Exception as e:
    print(f"ERROR: {e}")
