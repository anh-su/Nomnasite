"""
Translation log service — lưu lịch sử dịch của user.
Dùng Supabase khi _USE_CLOUD=True, fallback về SQLite local.
"""
import json
import sqlite3

DB_PATH = "database/dictionary.db"


def _conn():
    return sqlite3.connect(DB_PATH)


# ── Supabase client (lấy từ ocr_session để không init lại) ──────────────────

def _cloud():
    """Trả về (supa_client, True) nếu đang dùng Cloud, (None, False) nếu SQLite."""
    try:
        from services.ocr_session import _supa, _USE_CLOUD
        if _USE_CLOUD and _supa:
            return _supa, True
    except Exception:
        pass
    return None, False


# ── SQLite table ─────────────────────────────────────────────────────────────

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
    try:
        conn.execute("ALTER TABLE translation_log ADD COLUMN starred INTEGER DEFAULT 0")
    except Exception:
        pass
    conn.commit()
    conn.close()


# ── Public API ────────────────────────────────────────────────────────────────

def save_entry(username, input_text, output_text, direction):
    if not input_text or not output_text:
        return
    supa, use_cloud = _cloud()
    if use_cloud:
        try:
            res = supa.table("translation_log")\
                .select("input_text, output_text")\
                .eq("username", username)\
                .order("id", desc=True).limit(1).execute()
            if res.data:
                last = res.data[0]
                if last.get("input_text") == input_text and last.get("output_text") == output_text:
                    return
            supa.table("translation_log").insert({
                "username":    username,
                "input_text":  input_text,
                "output_text": output_text,
                "direction":   direction,
                "starred":     False,
            }).execute()
        except Exception:
            pass
        return
    conn = _conn()
    cur = conn.execute(
        "SELECT input_text, output_text FROM translation_log WHERE username=? ORDER BY id DESC LIMIT 1",
        (username,)
    )
    row = cur.fetchone()
    if row and row[0] == input_text and row[1] == output_text:
        conn.close()
        return
    conn.execute(
        "INSERT INTO translation_log (username, input_text, output_text, direction) VALUES (?,?,?,?)",
        (username, input_text, output_text, direction)
    )
    conn.commit()
    conn.close()


def get_entries(username, limit=8):
    supa, use_cloud = _cloud()
    if use_cloud:
        try:
            res = supa.table("translation_log")\
                .select("id, input_text, output_text, direction, starred, created_at")\
                .eq("username", username)\
                .order("id", desc=True).limit(limit).execute()
            return [
                {"id": r["id"], "input": r["input_text"], "output": r["output_text"],
                 "direction": r["direction"], "starred": bool(r.get("starred")), "time": r.get("created_at", "")}
                for r in (res.data or [])
            ]
        except Exception:
            return []
    conn = _conn()
    cur = conn.execute(
        "SELECT id, input_text, output_text, direction, starred, created_at FROM translation_log WHERE username=? ORDER BY id DESC LIMIT ?",
        (username, limit)
    )
    rows = cur.fetchall()
    conn.close()
    return [{"id": r[0], "input": r[1], "output": r[2],
             "direction": r[3], "starred": bool(r[4]), "time": r[5]} for r in rows]


def get_entry_by_id(entry_id):
    supa, use_cloud = _cloud()
    if use_cloud:
        try:
            res = supa.table("translation_log")\
                .select("id, input_text, output_text, direction, starred, created_at")\
                .eq("id", entry_id).limit(1).execute()
            if not res.data:
                return None
            r = res.data[0]
            return {"id": r["id"], "input": r["input_text"], "output": r["output_text"],
                    "direction": r["direction"], "starred": bool(r.get("starred")), "time": r.get("created_at", "")}
        except Exception:
            return None
    conn = _conn()
    cur = conn.execute(
        "SELECT id, input_text, output_text, direction, starred, created_at FROM translation_log WHERE id=?",
        (entry_id,)
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return {"id": row[0], "input": row[1], "output": row[2],
            "direction": row[3], "starred": bool(row[4]), "time": row[5]}


def delete_entry(entry_id):
    supa, use_cloud = _cloud()
    if use_cloud:
        try:
            supa.table("translation_log").delete().eq("id", entry_id).execute()
        except Exception:
            pass
        return
    conn = _conn()
    conn.execute("DELETE FROM translation_log WHERE id=?", (entry_id,))
    conn.commit()
    conn.close()


def toggle_star(entry_id):
    supa, use_cloud = _cloud()
    if use_cloud:
        try:
            res = supa.table("translation_log").select("starred").eq("id", entry_id).limit(1).execute()
            current = bool(res.data[0].get("starred")) if res.data else False
            supa.table("translation_log").update({"starred": not current}).eq("id", entry_id).execute()
        except Exception:
            pass
        return
    conn = _conn()
    conn.execute(
        "UPDATE translation_log SET starred = CASE WHEN starred=1 THEN 0 ELSE 1 END WHERE id=?",
        (entry_id,)
    )
    conn.commit()
    conn.close()


def sync_from_local(username, entries_json: str):
    """Đồng bộ entries từ localStorage vào DB, tránh trùng lặp."""
    try:
        entries = json.loads(entries_json)
    except Exception:
        return 0
    if not isinstance(entries, list):
        return 0

    supa, use_cloud = _cloud()
    if use_cloud:
        count = 0
        for e in reversed(entries):
            inp = e.get("input", "")
            out = e.get("output", "")
            if not inp or not out:
                continue
            try:
                supa.table("translation_log").insert({
                    "username":    username,
                    "input_text":  inp,
                    "output_text": out,
                    "direction":   e.get("direction", ""),
                    "starred":     bool(e.get("starred")),
                    "created_at":  e.get("time") or None,
                }).execute()
                count += 1
            except Exception:
                pass
        return count

    conn = _conn()
    count = 0
    for e in reversed(entries):
        inp = e.get("input", "")
        out = e.get("output", "")
        if not inp or not out:
            continue
        conn.execute(
            "INSERT INTO translation_log (username, input_text, output_text, direction, starred, created_at) VALUES (?,?,?,?,?,?)",
            (username, inp, out, e.get("direction", ""), 1 if e.get("starred") else 0, e.get("time", ""))
        )
        count += 1
    conn.commit()
    conn.close()
    return count


def count_all():
    """Tổng số entries — dùng cho admin stats."""
    supa, use_cloud = _cloud()
    if use_cloud:
        try:
            res = supa.table("translation_log").select("id", count="exact").execute()
            return res.count or 0
        except Exception:
            return 0
    conn = _conn()
    try:
        row = conn.execute("SELECT COUNT(*) FROM translation_log").fetchone()
        conn.close()
        return row[0] if row else 0
    except Exception:
        conn.close()
        return 0
