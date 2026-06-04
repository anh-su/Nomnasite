import sqlite3
import regex

DB_PATH = "database/dictionary.db"

_translations_cache = None


# =========================================
# CONNECT DATABASE
# =========================================

def get_connection():

    return sqlite3.connect(DB_PATH)


def _get_translations():
    global _translations_cache
    if _translations_cache is None:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT vietnamese, han_nom FROM translations")
        rows = cursor.fetchall()
        conn.close()
        _translations_cache = sorted(rows, key=lambda x: len(x[0]), reverse=True)
    return _translations_cache


# =========================================
# VIỆT -> HÁN NÔM
# =========================================

def translate_vi_to_hn(text):
    words = str(text).strip().lower().split()
    if not words:
        return ""

    lookup = {vi.lower(): hn for vi, hn in _get_translations()}
    result = []
    i = 0
    while i < len(words):
        matched = False
        # thử n-gram dài nhất trước (tối đa 4 từ)
        for n in range(min(4, len(words) - i), 0, -1):
            phrase = " ".join(words[i:i+n])
            if phrase in lookup:
                result.append(lookup[phrase])
                i += n
                matched = True
                break
        if not matched:
            result.append(words[i])  # giữ nguyên từ không dịch được
            i += 1

    return " ".join(result)


# =========================================
# HÁN NÔM -> VIỆT
# =========================================

def translate_hn_to_vi(text):

    conn = get_connection()

    cursor = conn.cursor()

    text = str(text)

    result = []

    for char in text:

        # bỏ mọi ký tự rác
        if char.strip() == "":
            continue

        cursor.execute("""
        SELECT vietnamese
        FROM translations
        WHERE han_nom = ?
        """, (char,))

        row = cursor.fetchone()

        if row:

            result.append(row[0])

        else:

            # giữ nguyên nếu chưa có DB
            result.append(char)

    conn.close()

    return " ".join(result)


# =========================================
# DETECT LANGUAGE
# =========================================

def detect_language(text):

    text = str(text)

    # detect tất cả chữ Hán/Nôm
    if regex.search(r'\p{Han}', text):

        return "han_nom"

    return "quoc_ngu"