#!/usr/bin/env python
"""
Database Setup Script for TaxMate AI
Initializes PostgreSQL database and creates all tables
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv
import psycopg2
from psycopg2 import sql
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# Database credentials
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "your_secure_password")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "taxmate_ai")
DATABASE_URL = os.getenv("DATABASE_URL")

# Colors for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_status(message, status="info"):
    """Print formatted status message"""
    if status == "success":
        print(f"{GREEN}✅ {message}{RESET}")
    elif status == "error":
        print(f"{RED}❌ {message}{RESET}")
    elif status == "warning":
        print(f"{YELLOW}⚠️  {message}{RESET}")
    elif status == "info":
        print(f"{BLUE}ℹ️  {message}{RESET}")


def check_env_file():
    """Check if .env file exists and has required variables"""
    print_status("Checking environment configuration...", "info")
    
    if not env_path.exists():
        print_status(".env file not found!", "error")
        print_status("Please create .env file using: cp .env.example .env", "warning")
        return False
    
    required_vars = ["DB_PASSWORD", "SECRET_KEY", "ENCRYPTION_KEY"]
    missing = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value or value.startswith("REPLACE_") or value == "your_secure_password":
            missing.append(var)
    
    if missing:
        print_status(f"Missing or placeholder values: {', '.join(missing)}", "error")
        print_status("Please update .env file with real values", "warning")
        return False
    
    print_status(".env file configured correctly", "success")
    return True


def connect_to_postgres():
    """Connect to PostgreSQL server (default database)"""
    print_status(f"Connecting to PostgreSQL at {DB_HOST}:{DB_PORT}...", "info")
    
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database="postgres"
        )
        conn.autocommit = True
        print_status(f"Connected to PostgreSQL", "success")
        return conn
    except psycopg2.Error as e:
        print_status(f"Failed to connect to PostgreSQL: {e}", "error")
        print_status("Make sure PostgreSQL is running and credentials are correct", "warning")
        return None


def create_database(conn):
    """Create the application database if it doesn't exist"""
    print_status(f"Creating database '{DB_NAME}' if not exists...", "info")
    
    try:
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(sql.SQL("SELECT 1 FROM pg_database WHERE datname = %s"), [DB_NAME])
        if cursor.fetchone():
            print_status(f"Database '{DB_NAME}' already exists", "success")
            cursor.close()
            return True
        
        # Create database
        cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DB_NAME)))
        print_status(f"Database '{DB_NAME}' created", "success")
        cursor.close()
        return True
        
    except psycopg2.Error as e:
        print_status(f"Failed to create database: {e}", "error")
        return False


def connect_to_app_database():
    """Connect to the application database"""
    print_status(f"Connecting to application database '{DB_NAME}'...", "info")
    
    try:
        engine = create_engine(
            DATABASE_URL,
            echo=False,
            pool_pre_ping=True
        )
        
        # Test connection
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        
        print_status(f"Connected to application database", "success")
        return engine
    except Exception as e:
        print_status(f"Failed to connect to application database: {e}", "error")
        return None


def create_tables(engine):
    """Create all application tables"""
    print_status("Creating application tables...", "info")
    
    try:
        # Import models to register them
        from app.models import Base
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        print_status("All tables created successfully", "success")
        return True
        
    except Exception as e:
        print_status(f"Failed to create tables: {e}", "error")
        return False


def verify_tables(engine):
    """Verify all expected tables were created"""
    print_status("Verifying table creation...", "info")
    
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        expected_tables = [
            "users",
            "tax_filings",
            "audit_flags",
            "benchmark_data",
            "token_blacklist"
        ]
        
        print_status(f"Found {len(tables)} tables", "info")
        
        for table in expected_tables:
            if table in tables:
                columns = inspector.get_columns(table)
                print_status(f"  ✓ {table} ({len(columns)} columns)", "success")
            else:
                print_status(f"  ✗ {table} not found!", "error")
                return False
        
        return True
        
    except Exception as e:
        print_status(f"Failed to verify tables: {e}", "error")
        return False


def get_table_info(engine):
    """Display detailed table information"""
    print_status("\n📋 Database Schema Summary:\n", "info")
    
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        for table in tables:
            columns = inspector.get_columns(table)
            print(f"  📌 {table}")
            for col in columns:
                nullable = "nullable" if col['nullable'] else "NOT NULL"
                print(f"     - {col['name']}: {col['type']} ({nullable})")
            print()
        
    except Exception as e:
        print_status(f"Failed to get table info: {e}", "error")


def test_database_operations(engine):
    """Test basic database operations"""
    print_status("\nTesting database operations...", "info")
    
    try:
        from sqlalchemy.orm import sessionmaker
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Test 1: Check database is writable
        result = session.execute(text("SELECT 1 as test"))
        if result.fetchone():
            print_status("  ✓ SELECT query works", "success")
        
        session.close()
        return True
        
    except Exception as e:
        print_status(f"Database operation test failed: {e}", "error")
        return False


def main():
    """Main setup routine"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}TaxMate AI - Database Setup{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    # Step 1: Check environment
    if not check_env_file():
        print_status("\n❌ Setup failed: Configure .env file first", "error")
        return False
    
    # Step 2: Connect to PostgreSQL
    conn = connect_to_postgres()
    if not conn:
        print_status("\n❌ Setup failed: Cannot connect to PostgreSQL", "error")
        print_status("Ensure PostgreSQL is running (docker or local)", "warning")
        return False
    
    # Step 3: Create database
    if not create_database(conn):
        conn.close()
        print_status("\n❌ Setup failed: Cannot create database", "error")
        return False
    
    conn.close()
    
    # Step 4: Connect to application database
    engine = connect_to_app_database()
    if not engine:
        print_status("\n❌ Setup failed: Cannot connect to app database", "error")
        return False
    
    # Step 5: Create tables
    if not create_tables(engine):
        print_status("\n❌ Setup failed: Cannot create tables", "error")
        return False
    
    # Step 6: Verify tables
    if not verify_tables(engine):
        print_status("\n❌ Setup failed: Table verification failed", "error")
        return False
    
    # Step 7: Display schema
    get_table_info(engine)
    
    # Step 8: Test operations
    if not test_database_operations(engine):
        print_status("⚠️  Database operations test failed", "warning")
    
    # Success
    print(f"\n{GREEN}{'='*60}{RESET}")
    print(f"{GREEN}✅ Database setup completed successfully!{RESET}")
    print(f"{GREEN}{'='*60}{RESET}\n")
    
    print_status("Database is ready for use", "success")
    print_status("You can now start the application", "info")
    print(f"\nTo run the application:")
    print(f"  docker-compose up")
    print(f"  # or")
    print(f"  uvicorn app.main:app --reload\n")
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print_status("\n\nSetup cancelled by user", "warning")
        sys.exit(1)
    except Exception as e:
        print_status(f"\n\nUnexpected error: {e}", "error")
        sys.exit(1)
