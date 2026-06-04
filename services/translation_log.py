import sqlite3
import json

DB_PATH = "database/dictionary.db"


def _conn():
    return sqlite3.connect(DB_PATH)


def create_table():
    conn = _conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS translation_log (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            username     TEXT NOT NULL,
            input_text   TEXT,
            output_text  TEXT,
            direction    TEXT,
            starred      INTEGER DEFAULT 0,
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # thêm cột starred nếu DB cũ chưa có
    try:
        conn.execute("ALTER TABLE translation_log ADD COLUMN starred INTEGER DEFAULT 0")
    except Exception:
        pass
    conn.commit()
    conn.close()


def save_entry(username, input_text, output_text, direction):
    if not input_text or not output_text:
        return
    conn = _conn()
    cur = conn.execute("""
        SELECT input_text, output_text FROM translation_log
        WHERE username=? ORDER BY id DESC LIMIT 1
    """, (username,))
    row = cur.fetchone()
    if row and row[0] == input_text and row[1] == output_text:
        conn.close()
        return
    conn.execute("""
        INSERT INTO translation_log (username, input_text, output_text, direction)
        VALUES (?, ?, ?, ?)
    """, (username, input_text, output_text, direction))
    conn.commit()
    conn.close()


def get_entries(username, limit=8):
    conn = _conn()
    cur = conn.execute("""
        SELECT id, input_text, output_text, direction, starred, created_at
        FROM translation_log
        WHERE username=?
        ORDER BY id DESC LIMIT ?
    """, (username, limit))
    rows = cur.fetchall()
    conn.close()
    return [
        {"id": r[0], "input": r[1], "output": r[2],
         "direction": r[3], "starred": bool(r[4]), "time": r[5]}
        for r in rows
    ]


def get_entry_by_id(entry_id):
    conn = _conn()
    cur = conn.execute("""
        SELECT id, input_text, output_text, direction, starred, created_at
        FROM translation_log WHERE id=?
    """, (entry_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return {"id": row[0], "input": row[1], "output": row[2],
            "direction": row[3], "starred": bool(row[4]), "time": row[5]}


def delete_entry(entry_id):
    conn = _conn()
    conn.execute("DELETE FROM translation_log WHERE id=?", (entry_id,))
    conn.commit()
    conn.close()


def toggle_star(entry_id):
    conn = _conn()
    conn.execute("""
        UPDATE translation_log
        SET starred = CASE WHEN starred=1 THEN 0 ELSE 1 END
        WHERE id=?
    """, (entry_id,))
    conn.commit()
    conn.close()


def sync_from_local(username, entries_json: str):
    """Đồng bộ entries từ localStorage (JSON string) vào DB, tránh trùng lặp."""
    try:
        entries = json.loads(entries_json)
    except Exception:
        return 0
    if not isinstance(entries, list):
        return 0

    conn = _conn()
    count = 0
    for e in reversed(entries):
        inp = e.get("input", "")
        out = e.get("output", "")
        direction = e.get("direction", "")
        t = e.get("time", "")
        starred = 1 if e.get("starred") else 0
        if not inp or not out:
            continue
        conn.execute("""
            INSERT INTO translation_log (username, input_text, output_text, direction, starred, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (username, inp, out, direction, starred, t))
        count += 1
    conn.commit()
    conn.close()
    return count
