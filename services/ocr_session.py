"""
OCR session service — lưu trữ phiên OCR và correction của user.

Ưu tiên Supabase (cloud) nếu SUPABASE_URL + SUPABASE_KEY có trong .env.
Fallback về SQLite local khi chưa cấu hình Supabase.
Supabase Storage dùng để lưu ảnh vĩnh viễn giữa các phiên.
"""

import os
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

_USE_CLOUD = False  # sẽ được gán lại sau khi _init_supabase() chạy


# ── Supabase Storage ──────────────────────────────────────────────────────────

_supa       = None
_BUCKET     = "ocr-images"
_CACHE_DIR  = Path(__file__).parent.parent / "data" / "ocr_images"


def _init_supabase():
    global _supa, _USE_CLOUD
    try:
        from supabase import create_client
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).parent.parent / ".env")
        _url = os.getenv("SUPABASE_URL", "").strip()
        _key = os.getenv("SUPABASE_KEY", "").strip()
        if _url and _key:
            _supa = create_client(_url, _key)
            _USE_CLOUD = True
            return True
    except Exception:
        pass
    return False


_init_supabase()


def upload_image(username: str, image_key: str, local_path: str) -> None:
    """Upload ảnh lên Supabase Storage (fire-and-forget, lỗi bị bỏ qua)."""
    if not _supa:
        return
    try:
        dest = f"{username}/{image_key}.jpg"
        with open(local_path, "rb") as f:
            data = f.read()
        _supa.storage.from_(_BUCKET).upload(
            dest, data,
            {"content-type": "image/jpeg", "upsert": "true"}
        )
    except Exception:
        pass


def download_image(username: str, image_key: str) -> str | None:
    """Tải ảnh từ Supabase Storage về cache local. Trả về đường dẫn hoặc None."""
    if not _supa:
        return None
    cache = _CACHE_DIR / f"{image_key}.jpg"
    if cache.exists():
        return str(cache)
    try:
        dest = f"{username}/{image_key}.jpg"
        data = _supa.storage.from_(_BUCKET).download(dest)
        if not data:
            return None
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache.write_bytes(data)
        return str(cache)
    except Exception:
        return None


# ── SQLite fallback ───────────────────────────────────────────────────────────

_SQLITE_PATH = "database/dictionary.db"


def _conn():
    return sqlite3.connect(_SQLITE_PATH)


def create_tables():
    """Tạo bảng SQLite (dùng khi Supabase chưa cấu hình)."""
    conn = _conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ocr_sessions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT NOT NULL,
            image_key   TEXT NOT NULL,
            image_name  TEXT DEFAULT '',
            doc_name    TEXT DEFAULT '',
            num_boxes   INTEGER DEFAULT 0,
            is_favorite INTEGER DEFAULT 0,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ocr_boxes (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id    INTEGER NOT NULL,
            box_index     INTEGER NOT NULL,
            nom_ocr       TEXT DEFAULT '',
            nom_corrected TEXT DEFAULT NULL,
            hanviet       TEXT DEFAULT '',
            accuracy      TEXT DEFAULT '',
            saved         INTEGER DEFAULT 0,
            updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            points        TEXT DEFAULT '',
            bbox_h        TEXT DEFAULT '',
            bbox_w        TEXT DEFAULT ''
        )
    """)
    # Migration: thêm các cột mới nếu DB cũ chưa có
    for _col, _tbl, _def in [
        ("is_favorite", "ocr_sessions", "INTEGER DEFAULT 0"),
        ("points",      "ocr_boxes",    "TEXT DEFAULT ''"),
        ("bbox_h",      "ocr_boxes",    "TEXT DEFAULT ''"),
        ("bbox_w",      "ocr_boxes",    "TEXT DEFAULT ''"),
    ]:
        try:
            conn.execute(f"ALTER TABLE {_tbl} ADD COLUMN {_col} {_def}")
            conn.commit()
        except Exception:
            pass
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_logins (
            username   TEXT PRIMARY KEY,
            email      TEXT DEFAULT '',
            last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _now_str():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def track_login(username: str, email: str = ""):
    """Ghi nhận lần đăng nhập — đảm bảo user xuất hiện trong danh sách admin."""
    now = _now_str()
    if _USE_CLOUD:
        try:
            _supa.table("user_logins").upsert(
                {"username": username, "email": email or username, "last_login": now},
                on_conflict="username"
            ).execute()
        except Exception:
            pass
        return
    conn = _conn()
    conn.execute("""
        INSERT INTO user_logins (username, email, last_login)
        VALUES (?, ?, ?)
        ON CONFLICT(username) DO UPDATE SET last_login=excluded.last_login, email=excluded.email
    """, (username, email or username, now))
    conn.commit()
    conn.close()


# ── Public API ────────────────────────────────────────────────────────────────

def find_session(username: str, image_key: str):
    """Trả về session_id nếu đã tồn tại, ngược lại None."""
    if _USE_CLOUD:
        res = (
            _supa.table("ocr_sessions")
            .select("id")
            .eq("username", username)
            .eq("image_key", image_key)
            .limit(1)
            .execute()
        )
        return res.data[0]["id"] if res.data else None
    # SQLite
    conn = _conn()
    cur = conn.execute(
        "SELECT id FROM ocr_sessions WHERE username=? AND image_key=? ORDER BY id DESC LIMIT 1",
        (username, image_key)
    )
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None


def get_or_create_session(username: str, image_key: str, image_name: str = '', num_boxes: int = 0):
    """Lấy session đã có hoặc tạo mới. Trả về session_id."""
    if _USE_CLOUD:
        existing = find_session(username, image_key)
        now = _now_str()
        if existing:
            _supa.table("ocr_sessions").update({"updated_at": now}).eq("id", existing).execute()
            return existing
        res = (
            _supa.table("ocr_sessions")
            .insert({
                "username":   username,
                "image_key":  image_key,
                "image_name": image_name,
                "doc_name":   "",
                "num_boxes":  num_boxes,
                "created_at": now,
                "updated_at": now,
            })
            .execute()
        )
        return res.data[0]["id"]

    # SQLite
    conn = _conn()
    cur = conn.execute(
        "SELECT id FROM ocr_sessions WHERE username=? AND image_key=? ORDER BY id DESC LIMIT 1",
        (username, image_key)
    )
    row = cur.fetchone()
    if row:
        session_id = row[0]
        conn.execute(
            "UPDATE ocr_sessions SET updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (session_id,)
        )
        conn.commit()
        conn.close()
        return session_id
    cur2 = conn.execute(
        "INSERT INTO ocr_sessions (username, image_key, image_name, num_boxes) VALUES (?,?,?,?)",
        (username, image_key, image_name, num_boxes)
    )
    session_id = cur2.lastrowid
    conn.commit()
    conn.close()
    return session_id


def update_session_doc(session_id, doc_name: str):
    if _USE_CLOUD:
        _supa.table("ocr_sessions").update({"doc_name": doc_name}).eq("id", session_id).execute()
        return
    conn = _conn()
    conn.execute("UPDATE ocr_sessions SET doc_name=? WHERE id=?", (doc_name, session_id))
    conn.commit()
    conn.close()


def save_boxes(session_id, ocr_data: list):
    """Lưu boxes lần đầu — không ghi đè correction đã có."""
    if _USE_CLOUD:
        res = (
            _supa.table("ocr_boxes")
            .select("id")
            .eq("session_id", session_id)
            .limit(1)
            .execute()
        )
        if res.data:
            return
        rows = [
            {
                "session_id":    session_id,
                "box_index":     i,
                "nom_ocr":       d.get("nom", ""),
                "nom_corrected": None,
                "hanviet":       d.get("modern", ""),
                "accuracy":      d.get("accuracy", ""),
                "saved":         False,
                "points":        d.get("points", ""),
                "bbox_h":        d.get("height", ""),
                "bbox_w":        d.get("width", ""),
            }
            for i, d in enumerate(ocr_data)
        ]
        if rows:
            try:
                _supa.table("ocr_boxes").insert(rows).execute()
            except Exception:
                # Fallback nếu Supabase chưa có cột mới
                rows_basic = [{k: v for k, v in r.items()
                               if k not in ('points', 'bbox_h', 'bbox_w')} for r in rows]
                if rows_basic:
                    _supa.table("ocr_boxes").insert(rows_basic).execute()
        return

    # SQLite
    conn = _conn()
    cur = conn.execute("SELECT COUNT(*) FROM ocr_boxes WHERE session_id=?", (session_id,))
    if cur.fetchone()[0] > 0:
        conn.close()
        return
    for i, d in enumerate(ocr_data):
        conn.execute(
            "INSERT INTO ocr_boxes "
            "(session_id, box_index, nom_ocr, hanviet, accuracy, points, bbox_h, bbox_w) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (session_id, i, d.get("nom", ""), d.get("modern", ""), d.get("accuracy", ""),
             d.get("points", ""), d.get("height", ""), d.get("width", ""))
        )
    conn.commit()
    conn.close()


def get_boxes(session_id) -> dict:
    """Dict: box_index(int) → {nom_ocr, nom_corrected, hanviet, accuracy, saved}."""
    if _USE_CLOUD:
        res = (
            _supa.table("ocr_boxes")
            .select("*")
            .eq("session_id", session_id)
            .order("box_index")
            .execute()
        )
        return {
            r["box_index"]: {
                "nom_ocr":       r.get("nom_ocr", ""),
                "nom_corrected": r.get("nom_corrected"),
                "hanviet":       r.get("hanviet", ""),
                "accuracy":      r.get("accuracy", ""),
                "saved":         bool(r.get("saved", False)),
                "points":        r.get("points", "") or "",
                "height":        r.get("bbox_h", "") or "",
                "width":         r.get("bbox_w", "") or "",
            }
            for r in res.data
        }

    # SQLite
    conn = _conn()
    cur = conn.execute(
        "SELECT box_index, nom_ocr, nom_corrected, hanviet, accuracy, saved, "
        "COALESCE(points,''), COALESCE(bbox_h,''), COALESCE(bbox_w,'') "
        "FROM ocr_boxes WHERE session_id=? ORDER BY box_index",
        (session_id,)
    )
    result = {}
    for row in cur.fetchall():
        result[row[0]] = {
            "nom_ocr": row[1], "nom_corrected": row[2],
            "hanviet": row[3], "accuracy": row[4], "saved": bool(row[5]),
            "points": row[6], "height": row[7], "width": row[8],
        }
    conn.close()
    return result


def save_correction(session_id, box_index: int, nom_corrected: str):
    if _USE_CLOUD:
        now = _now_str()
        _supa.table("ocr_boxes").update({
            "nom_corrected": nom_corrected,
            "saved":         True,
            "updated_at":    now,
        }).eq("session_id", session_id).eq("box_index", box_index).execute()
        _supa.table("ocr_sessions").update({"updated_at": now}).eq("id", session_id).execute()
        return

    # SQLite
    conn = _conn()
    conn.execute(
        "UPDATE ocr_boxes SET nom_corrected=?, saved=1, updated_at=CURRENT_TIMESTAMP "
        "WHERE session_id=? AND box_index=?",
        (nom_corrected, session_id, box_index)
    )
    conn.execute(
        "UPDATE ocr_sessions SET updated_at=CURRENT_TIMESTAMP WHERE id=?",
        (session_id,)
    )
    conn.commit()
    conn.close()


def get_sessions(username: str, limit: int = 20) -> list:
    """Danh sách sessions của user, kèm số box đã lưu."""
    if _USE_CLOUD:
        res = (
            _supa.table("ocr_sessions")
            .select("id, image_name, doc_name, num_boxes, created_at, updated_at, image_key, is_favorite")
            .eq("username", username)
            .order("updated_at", desc=True)
            .limit(limit)
            .execute()
        )
        sessions = res.data
        if not sessions:
            return []
        session_ids = [s["id"] for s in sessions]
        boxes_res = (
            _supa.table("ocr_boxes")
            .select("session_id, saved")
            .in_("session_id", session_ids)
            .execute()
        )
        total_map: dict = defaultdict(int)
        saved_map: dict = defaultdict(int)
        for b in boxes_res.data:
            sid = b["session_id"]
            total_map[sid] += 1
            if b["saved"]:
                saved_map[sid] += 1
        return [
            {
                "id":          s["id"],
                "image_name":  s["image_name"] or "",
                "doc_name":    s["doc_name"] or "",
                "num_boxes":   s["num_boxes"],
                "created_at":  s["created_at"] or "",
                "updated_at":  s["updated_at"] or "",
                "total_boxes": total_map[s["id"]],
                "saved_boxes": saved_map[s["id"]],
                "image_key":   s["image_key"] or "",
                "is_favorite": bool(s.get("is_favorite", False)),
            }
            for s in sessions
        ]

    # SQLite
    conn = _conn()
    cur = conn.execute("""
        SELECT s.id, s.image_name, s.doc_name, s.num_boxes, s.created_at, s.updated_at,
               COUNT(b.id) as total_boxes,
               COALESCE(SUM(b.saved), 0) as saved_boxes,
               s.image_key,
               COALESCE(s.is_favorite, 0) as is_favorite
        FROM ocr_sessions s
        LEFT JOIN ocr_boxes b ON b.session_id = s.id
        WHERE s.username=?
        GROUP BY s.id
        ORDER BY s.updated_at DESC
        LIMIT ?
    """, (username, limit))
    rows = cur.fetchall()
    conn.close()
    return [
        {"id": r[0], "image_name": r[1] or "", "doc_name": r[2] or "",
         "num_boxes": r[3], "created_at": r[4], "updated_at": r[5],
         "total_boxes": r[6], "saved_boxes": int(r[7]), "image_key": r[8] or "",
         "is_favorite": bool(r[9])}
        for r in rows
    ]


def get_session_boxes(session_id) -> list:
    """Tất cả boxes của một session để hiển thị lịch sử."""
    if _USE_CLOUD:
        res = (
            _supa.table("ocr_boxes")
            .select("*")
            .eq("session_id", session_id)
            .order("box_index")
            .execute()
        )
        return [
            {
                "box_index":     r["box_index"],
                "nom_ocr":       r.get("nom_ocr", ""),
                "nom_corrected": r.get("nom_corrected"),
                "hanviet":       r.get("hanviet", ""),
                "accuracy":      r.get("accuracy", ""),
                "saved":         bool(r.get("saved", False)),
                "updated_at":    r.get("updated_at") or "",
                "points":        r.get("points", "") or "",
                "height":        r.get("bbox_h", "") or "",
                "width":         r.get("bbox_w", "") or "",
            }
            for r in res.data
        ]

    # SQLite
    conn = _conn()
    cur = conn.execute(
        "SELECT box_index, nom_ocr, nom_corrected, hanviet, accuracy, saved, updated_at, "
        "COALESCE(points,''), COALESCE(bbox_h,''), COALESCE(bbox_w,'') "
        "FROM ocr_boxes WHERE session_id=? ORDER BY box_index",
        (session_id,)
    )
    rows = cur.fetchall()
    conn.close()
    return [
        {"box_index": r[0], "nom_ocr": r[1], "nom_corrected": r[2],
         "hanviet": r[3], "accuracy": r[4], "saved": bool(r[5]), "updated_at": r[6],
         "points": r[7], "height": r[8], "width": r[9]}
        for r in rows
    ]


def toggle_favorite(session_id) -> bool:
    """Đổi trạng thái yêu thích. Trả về giá trị mới."""
    if _USE_CLOUD:
        res = (
            _supa.table("ocr_sessions")
            .select("is_favorite")
            .eq("id", session_id)
            .limit(1)
            .execute()
        )
        current = bool(res.data[0]["is_favorite"]) if res.data else False
        new_val = not current
        _supa.table("ocr_sessions").update({"is_favorite": new_val}).eq("id", session_id).execute()
        return new_val
    # SQLite
    conn = _conn()
    cur = conn.execute("SELECT is_favorite FROM ocr_sessions WHERE id=?", (session_id,))
    row = cur.fetchone()
    current = bool(row[0]) if row else False
    new_val = not current
    conn.execute("UPDATE ocr_sessions SET is_favorite=? WHERE id=?", (int(new_val), session_id))
    conn.commit()
    conn.close()
    return new_val


def delete_session(session_id):
    if _USE_CLOUD:
        # ocr_boxes tự xóa cascade (FOREIGN KEY ON DELETE CASCADE)
        _supa.table("ocr_sessions").delete().eq("id", session_id).execute()
        return

    # SQLite
    conn = _conn()
    conn.execute("DELETE FROM ocr_boxes WHERE session_id=?", (session_id,))
    conn.execute("DELETE FROM ocr_sessions WHERE id=?", (session_id,))
    conn.commit()
    conn.close()
