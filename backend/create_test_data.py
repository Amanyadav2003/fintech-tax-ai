#!/usr/bin/env python3
"""Quick test to verify chat appears only after analysis"""
import os
from app.utils.database import SessionLocal
from app.models import User, TaxFiling
from app.utils.security import SecurityManager
from datetime import datetime

# Create test user
db = SessionLocal()
security = SecurityManager()

# Create user
user_data = {
    "email": os.getenv("TEST_DATA_EMAIL", "demo-user@example.invalid"),
    "password": os.getenv("TEST_DATA_PASSWORD", "TestOnly-Data-123!"),
    "name": "Demo User",
    "phone": "9999999999",
    "pan": "AABCD1234E",
    "age": 30,
    "state": "Delhi"
}

# Check if user exists
existing_user = db.query(User).filter(User.email == user_data["email"]).first()
if not existing_user:
    user = User(
        email=user_data["email"],
        password_hash=security.hash_password(user_data["password"]),
        name=user_data["name"],
        phone=user_data["phone"],
        pan=user_data["pan"],
        age=user_data["age"],
        state=user_data["state"]
    )
    db.add(user)
    db.commit()
    print(f"✅ Created user: {user_data['email']}")
else:
    user = existing_user
    print(f"✅ User already exists: {user_data['email']}")

# Create analysis for this user
existing_analysis = db.query(TaxFiling).filter(TaxFiling.user_id == user.id).first()
if not existing_analysis:
    analysis = TaxFiling(
        user_id=user.id,
        filing_year=2026,
        status="completed",
        salary=500000,
        total_income=500000,
        investments_80c=50000,
        health_insurance_80d=10000,
        total_deductions=60000,
        taxable_income=440000,
        tax_old_regime=94500,
        tax_new_regime=78750,
        recommended_regime="new"
    )
    db.add(analysis)
    db.commit()
    print(f"✅ Created tax filing for user ID: {user.id}")
else:
    print(f"✅ Tax filing already exists for user ID: {user.id}")

db.close()
print("\n✅ Test data ready! You can now:")
print(f"   Email: {user_data['email']}")
print(f"   Password: {user_data['password']}")
print("\nThe chat should appear ONLY after login and within the results/dashboard pages.")
