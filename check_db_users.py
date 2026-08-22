import sqlite3

conn = sqlite3.connect('backend/taxmate_ai.db')
cursor = conn.cursor()
cursor.execute('SELECT id, email, name FROM "user"')
users = cursor.fetchall()
print("Existing users in database:")
for user in users:
    print(f"  ID: {user[0]}, Email: {user[1]}, Name: {user[2]}")
conn.close()
