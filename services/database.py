import sqlite3

DB_PATH = "database/dictionary.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def _cloud():
    try:
        from services.ocr_session import _supa, _USE_CLOUD
        if _USE_CLOUD and _supa:
            return _supa, True
    except Exception:
        pass
    return None, False


# =========================
# OCR CORRECTIONS TABLE
# =========================
def create_tables():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS corrections (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        image_path TEXT,

        original_ocr_text TEXT,

        corrected_text TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )
    """)

    conn.commit()

    conn.close()


# =========================
# AI MEMORY TABLE
# =========================
def create_ai_tables():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ai_memory (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        nom_text TEXT,

        modern_meaning TEXT,

        poetic_translation TEXT,

        usage_count INTEGER DEFAULT 1,

        confidence REAL DEFAULT 1.0,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()

    conn.close()


# =========================
# OCR SUGGESTIONS
# =========================
def get_suggestions(ocr_text):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT corrected_text, COUNT(*) as total
        FROM corrections
        WHERE original_ocr_text = ?
        GROUP BY corrected_text
        ORDER BY total DESC
        LIMIT 10
    """, (ocr_text,))

    results = cursor.fetchall()

    conn.close()

    return [row[0] for row in results]


# =========================
# SAVE AI MEMORY
# =========================
def save_ai_memory(nom_text, meaning, poetry):
    supa, use_cloud = _cloud()
    if use_cloud:
        try:
            supa.table("ai_memory").upsert({
                "nom_text": nom_text,
                "modern_meaning": meaning,
                "poetic_translation": poetry,
            }, on_conflict="nom_text").execute()
        except Exception:
            pass
        return

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, usage_count FROM ai_memory WHERE nom_text=?", (nom_text,))
    row = cursor.fetchone()
    if row:
        cursor.execute(
            "UPDATE ai_memory SET modern_meaning=?, poetic_translation=?, usage_count=? WHERE id=?",
            (meaning, poetry, row[1] + 1, row[0])
        )
    else:
        cursor.execute(
            "INSERT INTO ai_memory (nom_text, modern_meaning, poetic_translation, usage_count) VALUES (?,?,?,?)",
            (nom_text, meaning, poetry, 1)
        )
    conn.commit()
    conn.close()


# =========================
# GET AI TRANSLATION
# =========================
def get_ai_translation(nom_text):
    supa, use_cloud = _cloud()

    # 1. Check ai_memory (Supabase or SQLite)
    if use_cloud:
        try:
            res = supa.table("ai_memory").select("modern_meaning, poetic_translation")\
                .eq("nom_text", nom_text).limit(1).execute()
            if res.data and res.data[0].get("modern_meaning"):
                r = res.data[0]
                return {"meaning": r["modern_meaning"], "phonetic": r.get("poetic_translation", ""), "found": True}
        except Exception:
            pass
    else:
        try:
            conn = get_connection()
            row = conn.execute(
                "SELECT modern_meaning, poetic_translation FROM ai_memory WHERE nom_text=? ORDER BY usage_count DESC LIMIT 1",
                (nom_text,)
            ).fetchone()
            conn.close()
            if row and row[0]:
                return {"meaning": row[0], "phonetic": row[1] or "", "found": True}
        except Exception:
            pass

    # 2. Check ai_translations (Supabase or SQLite)
    if use_cloud:
        try:
            res = supa.table("ai_translations").select("meaning, poetry")\
                .eq("nom_text", nom_text).limit(1).execute()
            if res.data and res.data[0].get("meaning"):
                r = res.data[0]
                return {"meaning": r["meaning"], "phonetic": r.get("poetry", ""), "found": True}
        except Exception:
            pass
    else:
        try:
            conn = sqlite3.connect("database/dictionary.db")
            row = conn.execute("SELECT meaning, poetry FROM ai_translations WHERE nom_text=? LIMIT 1", (nom_text,)).fetchone()
            conn.close()
            if row:
                return {"meaning": row[0], "phonetic": row[1] or "", "found": True}
        except Exception:
            pass

    return {"meaning": f"Chưa có dữ liệu cho: {nom_text}", "phonetic": f"Chưa có dữ liệu cho: {nom_text}", "found": False}
# =========================
# SAVE AI TRANSLATION (kết quả từ Claude)
# =========================
def save_ai_translation(nom_text, meaning, phonetic):
    supa, use_cloud = _cloud()
    if use_cloud:
        try:
            supa.table("ai_translations").upsert(
                {"nom_text": nom_text, "meaning": meaning, "poetry": phonetic},
                on_conflict="nom_text"
            ).execute()
        except Exception:
            pass
        return

    conn = sqlite3.connect("database/dictionary.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_translations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom_text TEXT UNIQUE,
            meaning TEXT,
            poetry TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("INSERT OR IGNORE INTO ai_translations (nom_text, meaning, poetry) VALUES (?,?,?)",
                   (nom_text, meaning, phonetic))
    conn.commit()
    conn.close()