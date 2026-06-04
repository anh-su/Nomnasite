import sqlite3, sys, os
sys.stdout.reconfigure(encoding='utf-8')

db = 'database/dictionary.db'
if not os.path.exists(db):
    print('DB KHONG TON TAI:', db)
    exit(1)

conn = sqlite3.connect(db)

def tbl_exists(name):
    return conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone() is not None

# 1. Kiem tra cac bang can cho tab Thong ke
print("=== KIEM TRA BANG DATABASE ===")
tables = ['ocr_sessions', 'ocr_boxes', 'translation_log', 'translations', 'ai_translations']
for t in tables:
    ok = tbl_exists(t)
    print(f"  {t:<22}: {'OK' if ok else 'THIEU !!!'}")

print()
print("=== CHAY QUERY _get_stats ===")
errors = []

def safe(desc, fn):
    try:
        val = fn()
        print(f"  {desc:<30}: {val}")
    except Exception as e:
        print(f"  {desc:<30}: ERROR - {e}")
        errors.append((desc, str(e)))

safe("ocr_sessions count",      lambda: conn.execute("SELECT COUNT(*) FROM ocr_sessions").fetchone()[0])
safe("ocr_boxes count",         lambda: conn.execute("SELECT COUNT(*) FROM ocr_boxes").fetchone()[0])
safe("ocr_boxes saved=1",       lambda: conn.execute("SELECT COUNT(*) FROM ocr_boxes WHERE saved=1").fetchone()[0])
safe("users distinct",          lambda: conn.execute("SELECT COUNT(DISTINCT username) FROM ocr_sessions").fetchone()[0])
safe("translation_log count",   lambda: conn.execute("SELECT COUNT(*) FROM translation_log").fetchone()[0])
safe("translations count",      lambda: conn.execute("SELECT COUNT(*) FROM translations").fetchone()[0])
safe("ai_translations count",   lambda: conn.execute("SELECT COUNT(*) FROM ai_translations").fetchone()[0])
safe("sessions today",          lambda: conn.execute(
    "SELECT COUNT(*) FROM ocr_sessions WHERE DATE(created_at)=DATE('now')"
).fetchone()[0])

print()
print("=== KIEM TRA COLUMNS ocr_boxes ===")
cols = conn.execute("PRAGMA table_info(ocr_boxes)").fetchall()
col_names = [c[1] for c in cols]
for c in cols:
    print(f"  {c[1]} ({c[2]})")

# Kiem tra cac column can cho _render_stats va _accuracy_dist
needed_cols = ['saved', 'accuracy', 'updated_at']
print()
print("=== COLUMNS CAN CHO TAB THONG KE ===")
for col in needed_cols:
    ok = col in col_names
    print(f"  ocr_boxes.{col:<12}: {'OK' if ok else 'THIEU !!!'}")

print()
print("=== KIEM TRA QUERY _accuracy_dist ===")
safe("accuracy rows (limit 5000)",
     lambda: len(conn.execute("SELECT accuracy FROM ocr_boxes WHERE accuracy != '' LIMIT 5000").fetchall()))

print()
print("=== KIEM TRA QUERY _user_list ===")
try:
    rows = conn.execute("""
        SELECT s.username,
               COUNT(DISTINCT s.id)   AS phien,
               SUM(b.saved)           AS da_luu,
               MAX(s.updated_at)      AS lan_cuoi
        FROM ocr_sessions s
        LEFT JOIN ocr_boxes b ON b.session_id = s.id
        GROUP BY s.username ORDER BY phien DESC
    """).fetchall()
    print(f"  _user_list query     : OK ({len(rows)} users)")
except Exception as e:
    print(f"  _user_list ERROR     : {e}")
    errors.append(("_user_list", str(e)))

print()
print("=== KIEM TRA QUERY _activity_7d ===")
try:
    rows = conn.execute("""
        SELECT DATE(created_at) AS ngay, COUNT(*) AS phien
        FROM ocr_sessions WHERE DATE(created_at) >= DATE('now', '-6 days')
        GROUP BY 1 ORDER BY 1
    """).fetchall()
    print(f"  _activity_7d query   : OK ({len(rows)} ngay)")
except Exception as e:
    print(f"  _activity_7d ERROR   : {e}")
    errors.append(("_activity_7d", str(e)))

conn.close()

print()
if errors:
    print(f"==> Co {len(errors)} LOI:")
    for d, e in errors:
        print(f"    - {d}: {e}")
else:
    print("==> Tat ca query OK, tab Thong ke co the hoat dong binh thuong.")
