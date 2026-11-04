import sqlite3
conn = sqlite3.connect("emp.db")

'''tables = conn.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type = 'table'
    AND name NOT LIKE 'sqlite_%'
    ORDER BY name
""").fetchall()

print("Tables found:", len(tables))

for table in tables:
    print(table[0])

conn.row_factory = sqlite3.Row
admin = conn.execute("""SELECT id, name, email, role, status, password_hash FROM users WHERE role = 'admin' """).fetchone()
if admin:
    print("Admin name:", admin["name"])
    print("Admin email:", admin["email"])
    print("Admin role:", admin["role"])
    print("Admin status:", admin["status"])
    print("Password hash stored:", bool(admin["password_hash"]))
else:
    print("Admin not found.")'''

examiner= conn.execute("""SELECT id, name, email, role, status FROM users WHERE role = 'examiner' """).fetchall()
print(examiner)
conn.close()
