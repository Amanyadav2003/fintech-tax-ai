#!/usr/bin/env python3
"""
Create chat_history table for storing chat conversations
Run this after adding ChatHistory model to the models
"""

from app.utils.database import engine
from app.models import Base, ChatHistory

def create_chat_history_table():
    """Create the chat_history table"""
    print("Creating chat_history table...")
    
    try:
        # Create all tables (including new ChatHistory)
        Base.metadata.create_all(bind=engine)
        print("✅ chat_history table created successfully!")
        
        # Show table info
        from sqlalchemy import inspect
        inspector = inspect(engine)
        columns = inspector.get_columns('chat_history')
        
        print("\nTable: chat_history")
        print("-" * 60)
        for col in columns:
            col_type = str(col['type'])
            nullable = "NULL" if col['nullable'] else "NOT NULL"
            print(f"  {col['name']:<20} {col_type:<15} {nullable}")
        
        print("-" * 60)
        print(f"Total columns: {len(columns)}")
        
    except Exception as e:
        print(f"❌ Error creating table: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_chat_history_table()
