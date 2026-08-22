import sqlite3
import json
from datetime import datetime

db_path = "backend/taxmate_ai.db"

html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TAXMATE AI - Database Viewer</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        h1 {
            color: white;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .stat-card h3 {
            color: #667eea;
            margin-bottom: 10px;
            font-size: 0.9em;
            text-transform: uppercase;
        }
        
        .stat-card .number {
            font-size: 2.5em;
            font-weight: bold;
            color: #333;
        }
        
        .table-container {
            background: white;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .table-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
        }
        
        .table-header h2 {
            font-size: 1.5em;
            margin: 0;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th {
            background: #f5f5f5;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            color: #333;
            border-bottom: 2px solid #ddd;
        }
        
        td {
            padding: 12px 15px;
            border-bottom: 1px solid #eee;
            color: #555;
        }
        
        tr:hover {
            background: #f9f9f9;
        }
        
        .empty {
            text-align: center;
            padding: 40px;
            color: #999;
            font-style: italic;
        }
        
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 500;
        }
        
        .badge-active {
            background: #d4edda;
            color: #155724;
        }
        
        .badge-verified {
            background: #cfe2ff;
            color: #084298;
        }
        
        .badge-inactive {
            background: #f8d7da;
            color: #842029;
        }
        
        footer {
            text-align: center;
            color: white;
            margin-top: 40px;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 TAXMATE AI - Database Viewer</h1>
        
        <div class="stats">
"""

# Connect to database and gather stats
try:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get counts for all tables
    cursor.execute("SELECT COUNT(*) as count FROM users")
    user_count = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM tax_filings")
    filing_count = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM audit_flags")
    flag_count = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM token_blacklist")
    token_count = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM benchmark_data")
    benchmark_count = cursor.fetchone()['count']
    
    # Add stat cards
    html_content += f"""
            <div class="stat-card">
                <h3>👥 Users</h3>
                <div class="number">{user_count}</div>
            </div>
            <div class="stat-card">
                <h3>📄 Tax Filings</h3>
                <div class="number">{filing_count}</div>
            </div>
            <div class="stat-card">
                <h3>⚠️ Audit Flags</h3>
                <div class="number">{flag_count}</div>
            </div>
            <div class="stat-card">
                <h3>🔐 Tokens Revoked</h3>
                <div class="number">{token_count}</div>
            </div>
            <div class="stat-card">
                <h3>📊 Benchmarks</h3>
                <div class="number">{benchmark_count}</div>
            </div>
        </div>
"""
    
    # USERS TABLE
    html_content += """
        <div class="table-container">
            <div class="table-header">
                <h2>👥 Users</h2>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Email</th>
                        <th>Name</th>
                        <th>Phone</th>
                        <th>PAN</th>
                        <th>Age</th>
                        <th>State</th>
                        <th>Status</th>
                        <th>Registered</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    cursor.execute("""
        SELECT id, email, name, phone, pan, age, state, is_active, is_verified, created_at 
        FROM users 
        ORDER BY id
    """)
    
    users = cursor.fetchall()
    if users:
        for user in users:
            active_badge = '<span class="badge badge-active">Active</span>' if user['is_active'] else '<span class="badge badge-inactive">Inactive</span>'
            verified_badge = '<span class="badge badge-verified">Verified</span>' if user['is_verified'] else ''
            html_content += f"""
                    <tr>
                        <td>{user['id']}</td>
                        <td><strong>{user['email']}</strong></td>
                        <td>{user['name']}</td>
                        <td>{user['phone']}</td>
                        <td>{user['pan']}</td>
                        <td>{user['age']}</td>
                        <td>{user['state']}</td>
                        <td>{active_badge} {verified_badge}</td>
                        <td>{user['created_at']}</td>
                    </tr>
"""
    else:
        html_content += '<tr><td colspan="9" class="empty">No users found</td></tr>'
    
    html_content += """
                </tbody>
            </table>
        </div>
"""
    
    # TAX FILINGS TABLE
    html_content += """
        <div class="table-container">
            <div class="table-header">
                <h2>📄 Tax Filings</h2>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>User</th>
                        <th>Year</th>
                        <th>Status</th>
                        <th>Salary</th>
                        <th>Total Income</th>
                        <th>Deductions</th>
                        <th>Tax (Old Regime)</th>
                        <th>Tax (New Regime)</th>
                        <th>Recommended</th>
                        <th>Created</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    cursor.execute("""
        SELECT id, user_id, filing_year, status, salary, total_income, total_deductions, 
               tax_old_regime, tax_new_regime, recommended_regime, created_at
        FROM tax_filings 
        ORDER BY id DESC
    """)
    
    filings = cursor.fetchall()
    if filings:
        for filing in filings:
            html_content += f"""
                    <tr>
                        <td>{filing['id']}</td>
                        <td>{filing['user_id']}</td>
                        <td>{filing['filing_year']}</td>
                        <td>{filing['status']}</td>
                        <td>₹{filing['salary']:,.2f}</td>
                        <td>₹{filing['total_income']:,.2f}</td>
                        <td>₹{filing['total_deductions']:,.2f}</td>
                        <td>₹{filing['tax_old_regime']:,.2f}</td>
                        <td>₹{filing['tax_new_regime']:,.2f}</td>
                        <td><strong>{filing['recommended_regime']}</strong></td>
                        <td>{filing['created_at']}</td>
                    </tr>
"""
    else:
        html_content += '<tr><td colspan="11" class="empty">No tax filings found - Submit income/deductions to create one</td></tr>'
    
    html_content += """
                </tbody>
            </table>
        </div>
"""
    
    # AUDIT FLAGS TABLE
    html_content += """
        <div class="table-container">
            <div class="table-header">
                <h2>⚠️ Audit Flags</h2>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Filing</th>
                        <th>Flag Type</th>
                        <th>Severity</th>
                        <th>Description</th>
                        <th>Recommendation</th>
                        <th>Created</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    cursor.execute("""
        SELECT id, filing_id, flag_type, severity, description, recommendation, created_at
        FROM audit_flags 
        ORDER BY id DESC
    """)
    
    flags = cursor.fetchall()
    if flags:
        for flag in flags:
            html_content += f"""
                    <tr>
                        <td>{flag['id']}</td>
                        <td>{flag['filing_id']}</td>
                        <td>{flag['flag_type']}</td>
                        <td>{flag['severity']}</td>
                        <td>{flag['description']}</td>
                        <td>{flag['recommendation']}</td>
                        <td>{flag['created_at']}</td>
                    </tr>
"""
    else:
        html_content += '<tr><td colspan="7" class="empty">No audit flags - Create a tax filing to generate audit analysis</td></tr>'
    
    html_content += """
                </tbody>
            </table>
        </div>
        
        <footer>
            <p>TAXMATE AI Database Viewer • SQLite 3 • Database: backend/taxmate_ai.db</p>
            <p>Last updated: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
        </footer>
    </div>
</body>
</html>
"""
    
    # Write HTML file
    with open("c:\\fintech-tax-ai\\database_viewer.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print("✅ Database viewer created: database_viewer.html")
    print("📍 Location: c:\\fintech-tax-ai\\database_viewer.html")
    print("\n🌐 To view, open the file in your browser")
    
    conn.close()
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
