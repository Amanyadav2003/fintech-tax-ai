import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.utils.security import SecurityManager
from app.models import User
from app.utils.database import SessionLocal

def create_user():
    db = SessionLocal()
    email = "testuser1@example.com"
    password = "Password123!"
    
    user = db.query(User).filter(User.email == email).first()
    if user:
        print("User already exists, updating password.")
        user.password_hash = SecurityManager.hash_password(password)
        db.commit()
    else:
        new_user = User(
            email=email,
            password_hash=SecurityManager.hash_password(password),
            name="Test User",
            phone="1234567890",
            pan="ABCDE1234F",
            age=30,
            state="Maharashtra",
            is_active=True
        )
        db.add(new_user)
        db.commit()
        print("Created new user.")
    
    db.close()
    print(f"Test user ready: {email} / {password}")

if __name__ == "__main__":
    create_user()
