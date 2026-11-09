import sqlite3

conn = sqlite3.connect('stockvision.db')
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables:", [t[0] for t in tables])

for t in tables:
    name = t[0]
    print(f"\n--- {name} ---")
    cursor.execute(f"SELECT COUNT(*) FROM [{name}]")
    print(f"Count: {cursor.fetchone()[0]}")
    cursor.execute(f"PRAGMA table_info([{name}])")
    cols = cursor.fetchall()
    col_names = [c[1] for c in cols]
    print(f"Columns: {col_names}")
    cursor.execute(f"SELECT * FROM [{name}] LIMIT 5")
    rows = cursor.fetchall()
    for r in rows:
        print(r)

conn.close()
