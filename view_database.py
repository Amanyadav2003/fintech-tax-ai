import sqlite3
import json
from datetime import datetime

db_path = "backend/taxmate_ai.db"

try:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("\n" + "="*120)
    print(" "*40 + "TAXMATE AI - DATABASE VIEWER")
    print("="*120)
    print(f"Database: {db_path}")
    print(f"Type: SQLite 3")
    print("="*120)
    
    # ==================== USERS TABLE ====================
    print("\n\n" + "█"*120)
    print("█ USERS TABLE")
    print("█"*120)
    
    cursor.execute("SELECT COUNT(*) as count FROM users")
    user_count = cursor.fetchone()['count']
    print(f"\nTotal Users: {user_count}\n")
    
    cursor.execute("""
        SELECT id, email, name, phone, pan, age, state, is_active, is_verified, created_at 
        FROM users 
        ORDER BY id
    """)
    
    users = cursor.fetchall()
    if users:
        print(f"{'ID':<4} {'Email':<30} {'Name':<20} {'Phone':<12} {'PAN':<12} {'Age':<4} {'State':<12} {'Active':<8} {'Verified':<10} {'Created':<19}")
        print("-"*120)
        for user in users:
            print(f"{user['id']:<4} {user['email']:<30} {user['name']:<20} {user['phone']:<12} {user['pan']:<12} {user['age']:<4} {user['state']:<12} {str(user['is_active']):<8} {str(user['is_verified']):<10} {user['created_at']:<19}")
    else:
        print("No users found")
    
    # ==================== TAX FILINGS TABLE ====================
    print("\n\n" + "█"*120)
    print("█ TAX FILINGS TABLE")
    print("█"*120)
    
    cursor.execute("SELECT COUNT(*) as count FROM tax_filings")
    filing_count = cursor.fetchone()['count']
    print(f"\nTotal Tax Filings: {filing_count}\n")
    
    cursor.execute("""
        SELECT id, user_id, filing_year, status, salary, total_income, total_deductions, 
               tax_old_regime, tax_new_regime, recommended_regime, created_at
        FROM tax_filings 
        ORDER BY id
    """)
    
    filings = cursor.fetchall()
    if filings:
        print(f"{'ID':<4} {'User':<5} {'Year':<6} {'Status':<12} {'Salary':<12} {'Income':<12} {'Deductions':<12} {'Old Tax':<12} {'New Tax':<12} {'Regime':<8} {'Created':<19}")
        print("-"*120)
        for filing in filings:
            print(f"{filing['id']:<4} {filing['user_id']:<5} {filing['filing_year']:<6} {filing['status']:<12} {filing['salary']:<12.2f} {filing['total_income']:<12.2f} {filing['total_deductions']:<12.2f} {filing['tax_old_regime']:<12.2f} {filing['tax_new_regime']:<12.2f} {filing['recommended_regime']:<8} {filing['created_at']:<19}")
    else:
        print("No tax filings found")
    
    # ==================== AUDIT FLAGS TABLE ====================
    print("\n\n" + "█"*120)
    print("█ AUDIT FLAGS TABLE")
    print("█"*120)
    
    cursor.execute("SELECT COUNT(*) as count FROM audit_flags")
    flag_count = cursor.fetchone()['count']
    print(f"\nTotal Audit Flags: {flag_count}\n")
    
    cursor.execute("""
        SELECT id, filing_id, flag_type, severity, description, created_at
        FROM audit_flags 
        ORDER BY id
    """)
    
    flags = cursor.fetchall()
    if flags:
        print(f"{'ID':<4} {'Filing':<8} {'Flag Type':<25} {'Severity':<10} {'Description':<60} {'Created':<19}")
        print("-"*120)
        for flag in flags:
            desc = flag['description'][:57] + "..." if len(flag['description'] or "") > 60 else flag['description']
            print(f"{flag['id']:<4} {flag['filing_id']:<8} {flag['flag_type']:<25} {flag['severity']:<10} {desc:<60} {flag['created_at']:<19}")
    else:
        print("No audit flags found")
    
    # ==================== TOKEN BLACKLIST TABLE ====================
    print("\n\n" + "█"*120)
    print("█ TOKEN BLACKLIST TABLE (Revoked Tokens)")
    print("█"*120)
    
    cursor.execute("SELECT COUNT(*) as count FROM token_blacklist")
    blacklist_count = cursor.fetchone()['count']
    print(f"\nTotal Blacklisted Tokens: {blacklist_count}\n")
    
    cursor.execute("""
        SELECT id, user_id, token_jti, blacklisted_at, expires_at
        FROM token_blacklist 
        ORDER BY id
    """)
    
    blacklist = cursor.fetchall()
    if blacklist:
        print(f"{'ID':<4} {'User':<5} {'Token JTI':<40} {'Blacklisted':<19} {'Expires':<19}")
        print("-"*120)
        for entry in blacklist:
            jti = entry['token_jti'][:37] + "..." if len(entry['token_jti'] or "") > 40 else entry['token_jti']
            print(f"{entry['id']:<4} {entry['user_id']:<5} {jti:<40} {entry['blacklisted_at']:<19} {entry['expires_at']:<19}")
    else:
        print("No blacklisted tokens (all users are logged in or have not logged out)")
    
    # ==================== BENCHMARK DATA TABLE ====================
    print("\n\n" + "█"*120)
    print("█ BENCHMARK DATA TABLE (Reference Deduction Amounts)")
    print("█"*120)
    
    cursor.execute("SELECT COUNT(*) as count FROM benchmark_data")
    benchmark_count = cursor.fetchone()['count']
    print(f"\nTotal Benchmark Records: {benchmark_count}\n")
    
    cursor.execute("""
        SELECT id, income_bracket_min, income_bracket_max, deduction_type, 
               median_amount, mean_amount, percentile_75, percentile_90, 
               audit_risk_percentage, year
        FROM benchmark_data 
        ORDER BY year DESC, income_bracket_min
    """)
    
    benchmarks = cursor.fetchall()
    if benchmarks:
        print(f"{'ID':<4} {'Income Min':<12} {'Income Max':<12} {'Deduction':<15} {'Median':<12} {'Mean':<12} {'P75':<12} {'P90':<12} {'Audit Risk':<12} {'Year':<6}")
        print("-"*120)
        for bm in benchmarks:
            print(f"{bm['id']:<4} {bm['income_bracket_min']:<12.0f} {bm['income_bracket_max']:<12.0f} {bm['deduction_type']:<15} {bm['median_amount']:<12.2f} {bm['mean_amount']:<12.2f} {bm['percentile_75']:<12.2f} {bm['percentile_90']:<12.2f} {bm['audit_risk_percentage']:<12.2f} {bm['year']:<6}")
    else:
        print("No benchmark data found")
    
    # ==================== SUMMARY ====================
    print("\n\n" + "="*120)
    print(" "*45 + "SUMMARY")
    print("="*120)
    print(f"Users:                {user_count}")
    print(f"Tax Filings:          {filing_count}")
    print(f"Audit Flags:          {flag_count}")
    print(f"Blacklisted Tokens:   {blacklist_count}")
    print(f"Benchmark Records:    {benchmark_count}")
    print("="*120 + "\n")
    
    conn.close()
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
