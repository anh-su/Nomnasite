import os
import sys
import sqlite3

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def detect_category(book_name):
    name = book_name.lower()

    if "kieu" in name:
        return "Thơ Nôm", "Truyện Kiều"

    if "luc van tien" in name:
        return "Thơ Nôm", "Lục Vân Tiên"

    if "dvsktt" in name:
        return "Lịch sử", "Đại Việt Sử Ký Toàn Thư"

    return "Khác", book_name


def import_all():

    archive_dir = "data/archive/Raw"
    conn = sqlite3.connect("database/dictionary.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ai_translations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom_text TEXT UNIQUE,
        meaning TEXT,
        poetry TEXT,
        category TEXT,
        source TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    total = 0

    for book in os.listdir(archive_dir):

        trans_path = os.path.join(
            archive_dir, book, "translation.txt"
        )

        if not os.path.exists(trans_path):
            continue

        category, source = detect_category(book)
        print(f"Đang import: {book} [{category}]...")
        count = 0

        with open(trans_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if "\t" not in line:
                    continue

                parts = line.split("\t")
                if len(parts) < 2:
                    continue

                nom = parts[0].strip()
                meaning = parts[1].strip()

                if not nom or not meaning:
                    continue

                try:
                    cursor.execute("""
                    INSERT OR IGNORE INTO ai_translations
                    (nom_text, meaning, poetry, category, source)
                    VALUES (?, ?, ?, ?, ?)
                    """, (nom, meaning, "", category, source))
                    count += 1

                except:
                    pass

        total += count
        print(f"  → {count} dòng")

    conn.commit()
    conn.close()

    print(f"\n✅ Hoàn thành! Tổng cộng: {total} dòng")
    print(f"📁 Lưu tại: database/dictionary.db")


if __name__ == "__main__":
    import_all()