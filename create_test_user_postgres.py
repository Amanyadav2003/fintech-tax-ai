#!/usr/bin/env python3
"""Create a test user in PostgreSQL database"""

from backend.app.utils.database import SessionLocal
from backend.app.models import User
from backend.app.utils.security import SecurityManager
from datetime import datetime

db = SessionLocal()

try:
    # Create a test user
    sm = SecurityManager()
    hashed_password = sm.hash_password("Omkartri@123")
    
    user = User(
        email="Omkartri07@gmail.com",
        name="Omkar Test",
        phone="+91 9876543210",
        pan="BYBPK8880K",  # Example PAN
        password_hash=hashed_password,
        created_at=datetime.utcnow()
    )
    
    db.add(user)
    db.commit()
    
    print("✓ Test user created successfully!")
    print(f"  Email: {user.email}")
    print(f"  Name: {user.name}")
    print(f"  PAN: {user.pan}")
    
except Exception as e:
    print(f"✗ Error creating user: {e}")
    db.rollback()
finally:
    db.close()
