import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('database/dictionary.db')

print("=== ocr_sessions (tat ca ban ghi) ===")
rows = conn.execute("SELECT id, username, doc_name, created_at, updated_at FROM ocr_sessions ORDER BY created_at").fetchall()
print(f"Tong so session: {len(rows)}")
for r in rows:
    print(f"  id={r[0]}  user='{r[1]}'  doc='{r[2]}'  created={r[3]}")

print()
print("=== Users theo bang ocr_sessions ===")
users = conn.execute("SELECT DISTINCT username FROM ocr_sessions").fetchall()
print(f"So tai khoan co session: {len(users)}")
for u in users:
    print(f"  '{u[0]}'")

print()
print("=== Kiem tra bang luu thong tin dang nhap (neu co) ===")
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print("Tat ca bang trong DB:")
for t in tables:
    n = t[0]
    count = conn.execute(f"SELECT COUNT(*) FROM [{n}]").fetchone()[0]
    print(f"  {n}: {count} ban ghi")

conn.close()
