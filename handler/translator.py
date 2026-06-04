import json
import os
import sqlite3
import time
import requests
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

# ===== DATASET (dictionary.db) =====

_DB = Path(__file__).parent.parent / "database" / "dictionary.db"
_phrase_phonetic: dict | None = None   # nom_text → phiên âm (ai_translations.meaning)
_phrase_meaning:  dict | None = None   # nom_text → dịch nghĩa (ai_translations.vi_meaning)
_char_dict:       dict | None = None   # han_nom  → [(han_viet, meaning), ...]
_hvdic_not_found: set         = set()  # chữ đã tra HVDIC nhưng không có kết quả

def _load_db():
    global _phrase_phonetic, _phrase_meaning, _char_dict
    if _phrase_phonetic is not None:
        return _phrase_phonetic, _phrase_meaning, _char_dict

    conn = sqlite3.connect(_DB)
    cur  = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS ai_translations (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            nom_text  TEXT UNIQUE,
            meaning   TEXT,
            vi_meaning TEXT,
            poetry    TEXT
        )
    """)
    conn.commit()

    cur.execute("SELECT nom_text, meaning, vi_meaning FROM ai_translations")
    _phrase_phonetic = {}
    _phrase_meaning  = {}
    for nom_text, meaning, vi_meaning in cur.fetchall():
        if meaning:
            _phrase_phonetic[nom_text] = meaning
        if vi_meaning:
            _phrase_meaning[nom_text] = vi_meaning

    cur.execute("SELECT han_nom, han_viet, meaning FROM translations")
    _char_dict = {}
    for han_nom, han_viet, meaning in cur.fetchall():
        _char_dict.setdefault(han_nom, []).append((han_viet or "", meaning or ""))

    conn.close()

    # Suy ra đơn chữ từ các cụm trong ai_translations:
    # nếu cụm n chữ có đúng n âm tiết phiên âm → map 1-1 từng chữ → âm/nghĩa
    inferred: dict[str, tuple[str, str]] = {}
    for nom_text, phonetic in _phrase_phonetic.items():
        chars = [c for c in nom_text if c.strip()]
        syllables = phonetic.strip().split()
        if len(chars) < 2 or len(chars) != len(syllables):
            continue
        vi_mean  = _phrase_meaning.get(nom_text, "")
        vi_words = vi_mean.strip().split() if vi_mean else []
        for i, (ch, syl) in enumerate(zip(chars, syllables)):
            if ch in _char_dict or ch in inferred:
                continue
            mn = vi_words[i] if len(vi_words) == len(chars) else ""
            inferred[ch] = (syl, mn)
    for ch, (hv, mn) in inferred.items():
        _char_dict[ch] = [(hv, mn)]

    return _phrase_phonetic, _phrase_meaning, _char_dict


def _hvdic_lookup_and_save(char: str) -> str:
    """Tra HVDIC cho một chữ đơn, lưu vào DB và cập nhật cache. Trả về phiên âm hoặc ''."""
    global _char_dict, _hvdic_not_found
    if char in _hvdic_not_found:
        return ""
    try:
        url = "https://hvdic.thivien.net/transcript-query.json.php"
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        han_viet = ""
        for lang in [1, 3]:
            payload = f"mode=trans&lang={lang}&input={char}"
            resp = requests.post(url, headers=headers, data=payload.encode(), timeout=5)
            result = json.loads(resp.text).get("result", [])
            for d in result:
                if isinstance(d, dict) and d.get("t") == 3 and d.get("o"):
                    han_viet = d["o"][0]
                    break
            if han_viet:
                break
        if not han_viet:
            _hvdic_not_found.add(char)
            return ""
        # Lưu vào DB
        conn = sqlite3.connect(str(_DB))
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM translations WHERE han_nom = ?", (char,))
        if cur.fetchone()[0] == 0:
            conn.execute(
                "INSERT INTO translations (han_nom, han_viet, meaning) VALUES (?, ?, ?)",
                (char, han_viet, "")
            )
            conn.commit()
        conn.close()
        # Cập nhật cache in-memory
        if _char_dict is not None:
            _char_dict[char] = [(han_viet, "")]
        return han_viet
    except Exception:
        _hvdic_not_found.add(char)
        return ""


def db_hanviet(text: str) -> str:
    """Phiên âm Hán Việt: tra cụm câu trước, fallback từng chữ, fallback HVDIC online."""
    phrase_phonetic, _, char_dict = _load_db()
    text = text.strip()

    if text in phrase_phonetic:
        return phrase_phonetic[text]

    parts = []
    for ch in text:
        if ch.strip() == "":
            continue
        entries = char_dict.get(ch, [])
        readings = [e[0] for e in entries if e[0]]
        if readings:
            parts.append(readings[0])
        else:
            hv = _hvdic_lookup_and_save(ch)
            parts.append(hv if hv else "[?]")
    result = " ".join(parts)
    return result if result.replace("[?]", "").strip() else "Không tìm thấy."


def db_meaning(text: str) -> str:
    """Dịch nghĩa: tra phrase-level trước, fallback từng chữ."""
    _, phrase_meaning, char_dict = _load_db()
    text = text.strip()

    # Phrase-level lookup (AI generated)
    if text in phrase_meaning:
        return phrase_meaning[text]

    # Fallback: từng chữ
    parts = []
    for ch in text:
        if ch.strip() == "":
            continue
        entries = char_dict.get(ch, [])
        meanings = [e[1] for e in entries if e[1]]
        if meanings:
            parts.append(meanings[0].lower())
        elif entries and entries[0][0]:
            parts.append(entries[0][0].lower())
        else:
            parts.append("[UNK]")
    return " ".join(parts) if parts else "Không tìm thấy trong bộ dữ liệu."


# ===== AI TRANSLATION (Groq) =====

@st.cache_data(show_spinner=False)
def ai_vi_to_nom(text: str) -> str:
    """Dịch tiếng Việt → chữ Hán Nôm: DB lookup trước, Groq dùng kết quả đó làm context."""
    from handler.dictionary_handler import translate_vi_to_hn
    db_result = translate_vi_to_hn(text)
    try:
        from groq import Groq
        client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": (
                    "Bạn là chuyên gia chữ Hán Nôm Việt Nam. "
                    "Dịch văn bản tiếng Việt sang chữ Hán Nôm cổ điển. "
                    "Chỉ trả về chữ Hán Nôm thuần túy, không giải thích, không phiên âm."
                )},
                {"role": "user", "content": (
                    f"Tiếng Việt: {text}\n"
                    f"Từ điển tra được (có thể chưa đầy đủ): {db_result}\n\n"
                    "Hãy hoàn thiện bản dịch sang chữ Hán Nôm chính xác nhất, "
                    "ưu tiên dùng các chữ đã tra được từ từ điển."
                )},
            ],
            temperature=0.1,
            max_tokens=500,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return db_result or f"[Lỗi AI: {e}]"


@st.cache_data(show_spinner=False)
def ai_nom_to_vi(text: str) -> str:
    """Dịch chữ Hán Nôm → tiếng Việt: DB lookup trước, Groq dùng kết quả đó làm context."""
    phienam = db_hanviet(text)
    nghia   = db_meaning(text)
    try:
        from groq import Groq
        client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": (
                    "Bạn là chuyên gia dịch Hán Nôm Việt Nam. "
                    "Dịch văn bản chữ Hán Nôm sang tiếng Việt hiện đại, dễ hiểu. "
                    "Trả về đúng 2 dòng:\nPhiên âm: [hán việt]\nDịch nghĩa: [tiếng việt hiện đại]"
                )},
                {"role": "user", "content": (
                    f"Chữ Nôm: {text}\n"
                    f"Phiên âm từ từ điển: {phienam}\n"
                    f"Nghĩa từng chữ từ từ điển: {nghia}\n\n"
                    "Dựa vào dữ liệu từ điển trên, hãy tổng hợp thành bản dịch tiếng Việt hiện đại hoàn chỉnh."
                )},
            ],
            temperature=0.2,
            max_tokens=500,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"Phiên âm: {phienam}\nDịch nghĩa: {nghia}"


# ===== API CŨ (giữ lại để tham khảo) =====

@st.cache_data(show_spinner=False)
def hcmus_translate(text):
    url = 'https://tools.clc.hcmus.edu.vn/api/web/clc-sinonom/sinonom-transliteration'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'content-type': 'application/json',
    }
    response = requests.request('POST', url, headers=headers, data=json.dumps({'text': text}))
    time.sleep(0.1)
    try:
        result = json.loads(response.text)['data']
        return result['result_text_transcription'][0].strip()
    except:
        return '"Không thể dịch văn bản này."'


@st.cache_data(show_spinner=False)
def hvdic_translate(text):
    def is_nom_text(result):
        for phonetics_dict in result:
            if phonetics_dict['t'] == 3 and len(phonetics_dict['o']) <= 0:
                return True
        return False

    url = 'https://hvdic.thivien.net/transcript-query.json.php'
    headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
    result = {}
    for lang in [1, 3]:
        payload = f'mode=trans&lang={lang}&input={text}'
        try:
            response = requests.request(
                'POST', url, headers=headers,
                data=payload.encode(), timeout=5
            )
            time.sleep(0.1)
            result = json.loads(response.text).get('result', {})
        except Exception:
            result = {}
            break
        if not is_nom_text(result):
            break
    return result


@st.cache_data(show_spinner=False)
def hvdic_render(text):
    phonetics = ''
    for d in hvdic_translate(text):
        if d['t'] == 3 and len(d['o']) > 0:
            if len(d['o']) == 1:
                phonetics += d['o'][0] + ' '
            else:
                phonetics += f'<select name="{d["o"][0]}">{"".join([f"<option><p>{o}</p></option>" for o in d["o"]])}</select>'
        else:
            phonetics += '[UNK] '
    return phonetics.strip() if phonetics else 'Không có phản hồi từ HVDIC.'
