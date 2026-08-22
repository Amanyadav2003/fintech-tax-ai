#!/usr/bin/env python
"""
Simple database reset script - DELETES ALL DATA
Run this to start fresh: python reset_db.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./taxmate_ai.db")

if DATABASE_URL.startswith("sqlite"):
    # SQLite: Delete the file
    db_path = DATABASE_URL.replace("sqlite:///", "")
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"✓ Deleted {db_path}")
    else:
        print(f"✓ Database file not found, will be created fresh")
else:
    # PostgreSQL: Drop and recreate all tables
    from sqlalchemy import create_engine, inspect, text
    try:
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        
        # Get all tables
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        with engine.connect() as conn:
            # Drop all tables
            for table in tables:
                print(f"Dropping table: {table}")
                conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
            conn.commit()
        
        print(f"✓ Dropped {len(tables)} tables from PostgreSQL")
    except Exception as e:
        print(f"✗ Error resetting PostgreSQL: {e}")
        sys.exit(1)

# Initialize fresh database
from app.utils.database import init_db
try:
    init_db()
    print("✓ Database initialized successfully")
    print("✓ Ready to start the application!")
except Exception as e:
    print(f"✗ Error initializing database: {e}")
    sys.exit(1)
