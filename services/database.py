import sqlite3

DB_PATH = "database/dictionary.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


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
def save_ai_memory(
    nom_text,
    meaning,
    poetry
):

    conn = get_connection()

    cursor = conn.cursor()

    # kiểm tra đã tồn tại chưa
    cursor.execute("""
    SELECT id, usage_count
    FROM ai_memory
    WHERE nom_text=?
    """, (nom_text,))

    row = cursor.fetchone()

    if row:

        memory_id = row[0]

        usage = row[1] + 1

        cursor.execute("""
        UPDATE ai_memory
        SET
            modern_meaning=?,
            poetic_translation=?,
            usage_count=?
        WHERE id=?
        """, (
            meaning,
            poetry,
            usage,
            memory_id
        ))

    else:

        cursor.execute("""
        INSERT INTO ai_memory (
            nom_text,
            modern_meaning,
            poetic_translation,
            usage_count
        )
        VALUES (?, ?, ?, ?)
        """, (
            nom_text,
            meaning,
            poetry,
            1
        ))

    conn.commit()

    conn.close()


# =========================
# GET AI TRANSLATION
# =========================
def get_ai_translation(nom_text):

    # =========================
    # 1. CHECK AI MEMORY (nom_ocr.db)
    # =========================
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT modern_meaning, poetic_translation
            FROM ai_memory
            WHERE nom_text = ?
            ORDER BY usage_count DESC
            LIMIT 1
        """, (nom_text,))
        row = cursor.fetchone()
        conn.close()
        if row and row[0]:
            return {
                "meaning": row[0],
                "phonetic": row[1] if row[1] else "",
                "found": True
            }
    except Exception:
        pass

    # =========================
    # 2. CHECK DICTIONARY.DB
    # =========================

    dict_conn = sqlite3.connect(
        "database/dictionary.db"
    )

    dict_cursor = dict_conn.cursor()

    dict_cursor.execute("""

    SELECT

        meaning,
        poetry

    FROM ai_translations

    WHERE nom_text=?

    LIMIT 1

    """, (nom_text,))

    dict_row = dict_cursor.fetchone()

    dict_conn.close()

    if dict_row:
        return {
            "meaning": dict_row[0],
            "phonetic": dict_row[1] if dict_row[1] else "",
            "found": True
        }


    # =========================
    # NOT FOUND
    # =========================

    return {

        "meaning": f"Chưa có dữ liệu cho: {nom_text}",

        "phonetic": f"Chưa có dữ liệu cho: {nom_text}",

        "found": False
    }
# =========================
# SAVE AI TRANSLATION (kết quả từ Claude)
# =========================
def save_ai_translation(nom_text, meaning, phonetic):

    conn = sqlite3.connect("database/dictionary.db")
    cursor = conn.cursor()

    # tạo bảng nếu chưa có
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ai_translations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom_text TEXT UNIQUE,
        meaning TEXT,
        poetry TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # nếu đã có thì bỏ qua, không ghi đè
    cursor.execute("""
    INSERT OR IGNORE INTO ai_translations (nom_text, meaning, poetry)
    VALUES (?, ?, ?)
    """, (nom_text, meaning, phonetic))

    conn.commit()
    conn.close()