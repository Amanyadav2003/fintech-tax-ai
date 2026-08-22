import sqlite3
from passlib.context import CryptContext

# Use the same context as the backend
pwd_context = CryptContext(schemes=["sha256_crypt", "bcrypt"], deprecated="auto")

db_path = "backend/taxmate_ai.db"

# New password for final@test.com
new_password = "Final@123"
password_hash = pwd_context.hash(new_password)

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Update the password for final@test.com
    cursor.execute("""
        UPDATE users 
        SET password_hash = ? 
        WHERE email = 'final@test.com'
    """, (password_hash,))
    
    conn.commit()
    
    print("✅ Password updated for final@test.com")
    print(f"New password: Final@123")
    print(f"\nYou can now login with:")
    print("  Email: final@test.com")
    print("  Password: Final@123")
    
    conn.close()
except Exception as e:
    print(f"ERROR: {e}")
