"""
Batch generate Vietnamese meanings for ai_translations using Groq API.
Run: python tools/generate_meanings.py
"""
import io
import json
import os
import re
import sqlite3
import sys
import time
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv
from groq import Groq

load_dotenv(Path(__file__).parent.parent / ".env")

DB         = Path(__file__).parent.parent / "database" / "dictionary.db"
BATCH_SIZE = 8
COMMIT_N   = 40   # commit every N successful batches

SYSTEM = (
    "Bạn là chuyên gia dịch Hán-Nôm sang tiếng Việt hiện đại. "
    "Luôn trả về JSON array thuần túy, không thêm giải thích. "
    "Mỗi phần tử là bản dịch nghĩa tiếng Việt ngắn gọn (tối đa 25 từ)."
)

def build_prompt(pairs):
    lines = [
        f'{i+1}. Nôm: "{nom}" | Phiên âm: "{phienam}"'
        for i, (nom, phienam) in enumerate(pairs)
    ]
    return (
        "Dịch nghĩa tiếng Việt hiện đại cho từng câu (JSON array theo đúng thứ tự):\n"
        + "\n".join(lines)
        + f'\n\nTrả về JSON array {len(pairs)} phần tử, ví dụ: ["nghĩa 1", "nghĩa 2"]'
    )

def parse_response(text, n):
    matches = list(re.finditer(r'\[', text))
    for m in reversed(matches):
        try:
            candidate = text[m.start():]
            result = json.loads(candidate[:candidate.rindex(']') + 1])
            if isinstance(result, list) and len(result) == n:
                return [str(r).strip() for r in result]
        except Exception:
            continue
    return None

def parse_retry_seconds(err_msg: str) -> float:
    """Parse 'try again in Xm Ys' from Groq error message."""
    m = re.search(r'try again in\s+((?:(\d+)m)?(?:\s*(\d+(?:\.\d+)?)s)?)', str(err_msg))
    if not m:
        return 5.0
    minutes = float(m.group(2) or 0)
    seconds = float(m.group(3) or 0)
    return minutes * 60 + seconds + 2  # +2s buffer

def main():
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    conn   = sqlite3.connect(DB)
    cur    = conn.cursor()

    cur.execute("""
        SELECT id, nom_text, meaning FROM ai_translations
        WHERE (vi_meaning IS NULL OR vi_meaning = '')
          AND meaning IS NOT NULL AND meaning != ''
        ORDER BY id
    """)
    rows = cur.fetchall()
    total = len(rows)
    print(f"Total to process: {total}")

    done = errors = 0
    pending = {}

    for start in range(0, total, BATCH_SIZE):
        batch  = rows[start : start + BATCH_SIZE]
        pairs  = [(r[1], r[2]) for r in batch]
        ids    = [r[0]         for r in batch]

        try:
            resp = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": SYSTEM},
                    {"role": "user",   "content": build_prompt(pairs)},
                ],
                temperature=0.2,
                max_tokens=800,
            )
            meanings = parse_response(resp.choices[0].message.content, len(batch))
        except Exception as e:
            err_str = str(e)
            # Hết hạn mức ngày → dừng hẳn, chạy lại ngày mai
            if 'tokens per day' in err_str.lower() or 'tpd' in err_str.lower():
                # Flush dữ liệu còn trong pending trước khi thoát
                if pending:
                    for rid, m in pending.items():
                        cur.execute("UPDATE ai_translations SET vi_meaning=? WHERE id=?", (m, rid))
                    conn.commit()
                    pending.clear()
                conn.close()
                print(f"\n[HẾT HẠN MỨC NGÀY] Đã sinh {done} nghĩa hôm nay.")
                print("Token/ngày đã đạt giới hạn 500,000. Chạy lại script vào ngày mai.")
                return
            # Rate limit tạm thời (per-minute) → sleep đúng thời gian Groq yêu cầu
            wait = parse_retry_seconds(err_str)
            print(f"  Rate limit batch {start}, chờ {wait:.0f}s...")
            time.sleep(wait)
            meanings = None
            errors += len(batch)
            continue

        if meanings:
            for rid, m in zip(ids, meanings):
                pending[rid] = m
            done += len(batch)
        else:
            errors += len(batch)

        if len(pending) >= COMMIT_N * BATCH_SIZE:
            for rid, m in pending.items():
                cur.execute("UPDATE ai_translations SET vi_meaning=? WHERE id=?", (m, rid))
            conn.commit()
            pending.clear()
            pct = done / total * 100
            print(f"  [{pct:.1f}%] {done}/{total} done, {errors} errors")

        time.sleep(0.05)

    if pending:
        for rid, m in pending.items():
            cur.execute("UPDATE ai_translations SET vi_meaning=? WHERE id=?", (m, rid))
        conn.commit()

    conn.close()
    print(f"\nFinished: {done} generated, {errors} errors / {total} total.")

if __name__ == "__main__":
    main()
