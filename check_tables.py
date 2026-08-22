import sqlite3

conn = sqlite3.connect('backend/taxmate_ai.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables in database:")
for table in tables:
    print(f"  - {table[0]}")
    
# Try to get users from each table
for table_name in [t[0] for t in tables]:
    if 'user' in table_name.lower():
        print(f"\nUsers in table '{table_name}':")
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
        rows = cursor.fetchall()
        for row in rows:
            print(f"  {row}")

conn.close()
