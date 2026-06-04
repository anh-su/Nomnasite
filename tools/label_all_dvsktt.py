"""
Gán nhãn toàn bộ patch DVSKTT (chính xác + ước lượng).

Bước 1 — Nhãn chính xác: cột khớp đúng trong JSON → patch_idx = col - 1
Bước 2 — Nhãn ước lượng: trang có JSON nhưng cột bị thiếu → lấy text cột gần nhất
Bước 3 — Patch trang không có JSON → bỏ qua (không có dữ liệu)

Kết quả ghi vào: data/archive/Patches/{book}/labels.txt
Patch ước lượng được đánh dấu bằng metadata riêng (không ảnh hưởng nhãn).
"""
import json
import os
import re

RAW_BASE   = "data/archive/Raw"
PATCH_BASE = "data/archive/Patches"

BOOKS = [
    "DVSKTT-1 Quyen thu",
    "DVSKTT-2 Ngoai ky toan thu",
    "DVSKTT-3 Ban ky toan thu",
    "DVSKTT-4 Ban ky thuc luc",
    "DVSKTT-5 Ban ky tuc bien",
]


def extract_col_text(text: str) -> dict:
    """Trả về {col: text} từ text 1 trang, nhiều dòng cùng cột thì ghép theo row."""
    col_map: dict[int, list] = {}
    for line in text.split("\n"):
        line = line.strip()
        m = re.search(r"\.\s*\[(\w+)\*(\d+)\*(\d+)\]", line)
        if not m:
            continue
        col = int(m.group(2))
        row = int(m.group(3))
        clean = re.sub(r"\s*\.\s*\[[^\]]+\]", "", line)
        clean = re.sub(r"\s+", "", clean).strip()
        if clean:
            col_map.setdefault(col, []).append((row, clean))
    return {col: "".join(t for _, t in sorted(entries))
            for col, entries in col_map.items()}


def nearest_col_text(col_text: dict, target_col: int) -> str:
    """Tìm text của cột gần nhất với target_col."""
    if not col_text:
        return ""
    cols = sorted(col_text.keys())
    left  = [c for c in cols if c <= target_col]
    right = [c for c in cols if c > target_col]
    if left:
        return col_text[left[-1]]
    if right:
        return col_text[right[0]]
    return ""


def load_json_pages(raw_dir: str) -> dict:
    """Đọc tất cả JSON → {page_name: {col: text}}."""
    page_col_text: dict[str, dict] = {}
    for jf in sorted(f for f in os.listdir(raw_dir) if f.endswith(".json")):
        data = json.load(open(os.path.join(raw_dir, jf), encoding="utf-8"))
        for entry in data:
            url  = entry.get("url", "")
            page = os.path.splitext(os.path.basename(url))[0]
            ct   = extract_col_text(entry.get("text", ""))
            if page not in page_col_text:
                page_col_text[page] = {}
            page_col_text[page].update(ct)
    return page_col_text


def process_book(book: str):
    raw_dir   = os.path.join(RAW_BASE, book)
    patch_dir = os.path.join(PATCH_BASE, book)
    out_path  = os.path.join(patch_dir, "labels.txt")

    if not os.path.isdir(raw_dir) or not os.path.isdir(patch_dir):
        print(f"  [SKIP] {book} — thu muc khong ton tai")
        return 0, 0, 0

    page_col_text = load_json_pages(raw_dir)
    all_patches   = sorted(f for f in os.listdir(patch_dir) if f.endswith(".jpg"))

    exact_labels:     dict[str, str] = {}
    estimated_labels: dict[str, str] = {}
    skipped = 0

    for fname in all_patches:
        parts = fname.rsplit("_", 1)
        if len(parts) != 2:
            continue
        page_name = parts[0]
        try:
            patch_idx = int(parts[1].replace(".jpg", ""))
        except ValueError:
            continue

        col_needed = patch_idx + 1
        ct = page_col_text.get(page_name, {})

        if not ct:
            # Trang không có trong JSON — bỏ qua
            skipped += 1
            continue

        if col_needed in ct:
            exact_labels[fname] = ct[col_needed]
        else:
            est = nearest_col_text(ct, col_needed)
            if est:
                estimated_labels[fname] = est
            else:
                skipped += 1

    # Gộp: chính xác trước, ước lượng sau
    combined = {**exact_labels, **estimated_labels}

    with open(out_path, "w", encoding="utf-8") as f:
        for fname, label in sorted(combined.items()):
            f.write(f"{fname}|{label}\n")

    print(f"  {book}:")
    print(f"    Chinh xac : {len(exact_labels):6}")
    print(f"    Uoc luong : {len(estimated_labels):6}")
    print(f"    Bo qua    : {skipped:6}  (trang khong co JSON)")
    print(f"    => Tong   : {len(combined):6}  -> {out_path}")
    return len(exact_labels), len(estimated_labels), skipped


def main():
    print("=== Gan nhan toan bo patch DVSKTT ===\n")

    total_exact = total_est = total_skip = 0
    for book in BOOKS:
        e, est, sk = process_book(book)
        total_exact += e
        total_est   += est
        total_skip  += sk
        print()

    total = total_exact + total_est
    print("=" * 50)
    print(f"Chinh xac  : {total_exact:7}")
    print(f"Uoc luong  : {total_est:7}")
    print(f"Bo qua     : {total_skip:7}")
    print(f"TONG       : {total:7}")

    print("\n--- Kiem tra toan bo archive/Patches ---")
    grand = 0
    for book in sorted(os.listdir(PATCH_BASE)):
        lbl = os.path.join(PATCH_BASE, book, "labels.txt")
        if os.path.exists(lbl):
            n = sum(1 for l in open(lbl, encoding="utf-8") if "|" in l)
            grand += n
            print(f"  {book}: {n}")
    print(f"\n  TONG CO NHAN: {grand}")


if __name__ == "__main__":
    main()
