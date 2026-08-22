import sqlite3

db_path = "backend/taxmate_ai.db"

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=" * 80)
    print("DATABASE: taxmate_ai.db (SQLite)")
    print(f"Location: {db_path}")
    print("=" * 80)
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    
    print(f"\nTOTAL TABLES: {len(tables)}\n")
    
    for table in tables:
        table_name = table[0]
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        
        # Get column info
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        print(f"{'='*80}")
        print(f"TABLE: {table_name}")
        print(f"Rows: {row_count}")
        print(f"{'='*80}")
        print(f"{'Column Name':<25} {'Type':<15} {'Nullable':<12} {'Primary Key'}")
        print(f"{'-'*25} {'-'*15} {'-'*12} {'-'*12}")
        
        for col in columns:
            col_id, col_name, col_type, not_null, default_val, pk = col
            nullable = "NO" if not_null else "YES"
            is_pk = "YES" if pk else "NO"
            print(f"{col_name:<25} {col_type:<15} {nullable:<12} {is_pk}")
        
        print()
    
    conn.close()
    
except Exception as e:
    print(f"ERROR: {e}")
