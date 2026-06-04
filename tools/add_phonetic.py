import os
import sys
import json
import time
import sqlite3

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def get_phonetic(nom_text):
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{
                "role": "user",
                "content": (
                    f"Cho phiên âm Hán-Việt của chữ Nôm sau: {nom_text}\n"
                    f"Trả về JSON, không giải thích:\n"
                    f'{{"phonetic": "phiên âm"}}'
                )
            }],
            max_tokens=100
        )
        text = response.choices[0].message.content.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text).get("phonetic", "")
    except Exception as e:
        return None  # None = lỗi, "" = không có phiên âm


def run():
    conn = sqlite3.connect("database/dictionary.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, nom_text FROM ai_translations
        WHERE poetry IS NULL OR poetry = ''
        ORDER BY id
    """)
    rows = cursor.fetchall()

    total = len(rows)
    print(f"Cần bổ sung phiên âm cho {total} dòng")
    print("Nhấn Ctrl+C để dừng, chạy lại sẽ tiếp tục từ chỗ dừng\n")

    done = 0
    errors = 0

    for i, (row_id, nom_text) in enumerate(rows):

        phonetic = None
        retries = 3

        for attempt in range(retries):
            phonetic = get_phonetic(nom_text)

            if phonetic is not None:
                break

            wait = 60 * (attempt + 1)  # 60s, 120s, 180s
            print(f"  ⚠️  Rate limit, chờ {wait} giây... (lần {attempt+1})")
            time.sleep(wait)

        if phonetic is None:
            errors += 1
            print(f"  ❌ Bỏ qua: {nom_text}")
            continue

        cursor.execute("""
            UPDATE ai_translations SET poetry = ? WHERE id = ?
        """, (phonetic, row_id))

        done += 1

        if done % 50 == 0:
            conn.commit()
            print(f"  ✅ {done}/{total} | lỗi: {errors} | đang xử lý id={row_id}")

        # Nghỉ 4 giây mỗi request — Groq free ~15 req/phút
        time.sleep(4)

    conn.commit()
    conn.close()
    print(f"\n🎉 Hoàn thành! {done} dòng, {errors} lỗi bỏ qua")

if __name__ == "__main__":
    run()