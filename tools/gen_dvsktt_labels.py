"""
Sinh labels.txt cho các tập DVSKTT dựa vào file JSON trong Raw/.
Nguyên tắc: column_number - 1 = patch_index
Nhiều dòng cùng cột → ghép lại theo thứ tự row.
"""
import json
import os
import re


BOOKS = {
    "DVSKTT-1 Quyen thu":        "DVSKTT-1 Quyen thu",
    "DVSKTT-2 Ngoai ky toan thu": "DVSKTT-2 Ngoai ky toan thu",
    "DVSKTT-3 Ban ky toan thu":   "DVSKTT-3 Ban ky toan thu",
    "DVSKTT-4 Ban ky thuc luc":   "DVSKTT-4 Ban ky thuc luc",
    "DVSKTT-5 Ban ky tuc bien":   "DVSKTT-5 Ban ky tuc bien",
}

RAW_BASE   = "data/archive/Raw"
PATCH_BASE = "data/archive/Patches"


def extract_col_lines(text: str) -> dict:
    """
    Trả về {col: [(row, hannom_text), ...]} từ text của 1 trang.
    """
    col_map: dict[int, list] = {}
    for line in text.split("\n"):
        line = line.strip()
        m = re.search(r"\.\s*\[(\w+)\*(\d+)\*(\d+)\]", line)
        if not m:
            continue
        col  = int(m.group(2))
        row  = int(m.group(3))
        # Xoá position marker và khoảng trắng giữa ký tự
        clean = re.sub(r"\s*\.\s*\[[^\]]+\]", "", line)
        clean = re.sub(r"\s+", "", clean).strip()
        if not clean:
            continue
        col_map.setdefault(col, []).append((row, clean))
    return col_map


def col_to_label(col_map: dict) -> dict:
    """
    {col: [(row, text)]} → {patch_index: label}
    patch_index = col - 1
    Nhiều dòng cùng cột → sắp xếp theo row rồi ghép.
    """
    result = {}
    for col, entries in col_map.items():
        patch_idx = col - 1
        entries_sorted = sorted(entries, key=lambda x: x[0])
        label = "".join(t for _, t in entries_sorted)
        result[patch_idx] = label
    return result


def process_book(book_name: str):
    raw_dir   = os.path.join(RAW_BASE, book_name)
    patch_dir = os.path.join(PATCH_BASE, book_name)
    out_path  = os.path.join(patch_dir, "labels.txt")

    if not os.path.isdir(raw_dir) or not os.path.isdir(patch_dir):
        print(f"  [SKIP] {book_name} — thư mục không tồn tại")
        return 0, 0

    json_files = sorted(f for f in os.listdir(raw_dir) if f.endswith(".json"))
    if not json_files:
        print(f"  [SKIP] {book_name} — không có file JSON")
        return 0, 0

    # Thu thập tất cả patch images hiện có
    all_patches = set(
        f for f in os.listdir(patch_dir)
        if f.endswith(".jpg")
    )

    labels: dict[str, str] = {}
    pages_ok   = 0
    pages_skip = 0

    for jf in json_files:
        data = json.load(open(os.path.join(raw_dir, jf), encoding="utf-8"))
        for entry in data:
            url       = entry.get("url", "")
            page_name = os.path.splitext(os.path.basename(url))[0]
            text      = entry.get("text", "")

            col_map   = extract_col_lines(text)
            patch_map = col_to_label(col_map)

            added = 0
            for patch_idx, label in patch_map.items():
                fname = f"{page_name}_{patch_idx}.jpg"
                if fname in all_patches:
                    labels[fname] = label
                    added += 1

            if added > 0:
                pages_ok += 1
            else:
                pages_skip += 1

    # Ghi labels.txt
    with open(out_path, "w", encoding="utf-8") as f:
        for fname, label in sorted(labels.items()):
            f.write(f"{fname}|{label}\n")

    print(f"  {book_name}: {len(labels)} nhãn / {pages_ok} trang OK / {pages_skip} trang bỏ qua")
    return len(labels), pages_ok


def main():
    print("=== Sinh labels.txt cho DVSKTT ===\n")
    total_labels = 0
    for book_name in BOOKS:
        n, _ = process_book(book_name)
        total_labels += n

    print(f"\nTổng nhãn sinh được: {total_labels}")
    print("\nKiểm tra lại toàn bộ dataset:")

    def count_labels(path):
        if not os.path.exists(path):
            return 0
        return sum(1 for l in open(path, encoding="utf-8") if "|" in l)

    grand = 0
    for book in sorted(os.listdir(PATCH_BASE)):
        lbl = os.path.join(PATCH_BASE, book, "labels.txt")
        n   = count_labels(lbl)
        grand += n
        if n:
            print(f"  {book}: {n}")

    ref = count_labels("data/reference_chars/labels.txt")
    print(f"  reference_chars: {ref}")
    print(f"\nTổng có nhãn: {grand + ref}")


if __name__ == "__main__":
    main()
