import os
import sqlite3
from passlib.context import CryptContext

# Use the same context as the backend
pwd_context = CryptContext(schemes=["sha256_crypt", "bcrypt"], deprecated="auto")

db_path = "backend/taxmate_ai.db"

# Configure the test identity instead of embedding credentials.
target_email = os.getenv("TEST_RESET_EMAIL", "final-user@example.invalid")
new_password = os.getenv("TEST_RESET_PASSWORD", "TestOnly-Reset-123!")
password_hash = pwd_context.hash(new_password)

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Update the configured test identity.
    cursor.execute("""
        UPDATE users 
        SET password_hash = ? 
        WHERE email = ?
    """, (password_hash, target_email))
    
    conn.commit()
    
    print(f"✅ Password updated for {target_email}")
    print("New password was supplied through TEST_RESET_PASSWORD.")
    print(f"\nYou can now login with:")
    print(f"  Email: {target_email}")
    print("  Password: supplied through TEST_RESET_PASSWORD")
    
    conn.close()
except Exception as e:
    print(f"ERROR: {e}")
