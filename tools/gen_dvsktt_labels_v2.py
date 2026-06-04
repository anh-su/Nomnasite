"""
Gán nhãn ước lượng cho 12.361 patch DVSKTT chưa có nhãn.
Lưu kết quả vào thư mục TEST riêng, KHÔNG ghi đè labels.txt gốc.

Nguyên tắc:
- Cột bị thiếu → tìm câu dài nhất cùng trang có col gần nhất
- Nếu col X bị thiếu, lấy text của col gần nhất bên trái (col < X)
- Kết quả lưu vào: data/archive/Patches_test/{book}/labels_estimated.txt
"""
import json, os, re

RAW_BASE    = "data/archive/Raw"
PATCH_BASE  = "data/archive/Patches"
TEST_BASE   = "data/archive/Patches_test"   # THƯ MỤC TEST RIÊNG

BOOKS = [
    "DVSKTT-1 Quyen thu",
    "DVSKTT-2 Ngoai ky toan thu",
    "DVSKTT-3 Ban ky toan thu",
    "DVSKTT-4 Ban ky thuc luc",
    "DVSKTT-5 Ban ky tuc bien",
]


def extract_col_text(text: str) -> dict:
    """Trả về {col: text} — nhiều dòng cùng cột thì ghép theo row."""
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
    result = {}
    for col, entries in col_map.items():
        result[col] = "".join(t for _, t in sorted(entries))
    return result


def nearest_col_text(col_text: dict, target_col: int) -> str:
    """Tìm text của cột gần nhất với target_col."""
    if not col_text:
        return ""
    cols = sorted(col_text.keys())
    # Ưu tiên cột bên trái gần nhất
    left  = [c for c in cols if c <= target_col]
    right = [c for c in cols if c > target_col]
    if left:
        return col_text[left[-1]]
    if right:
        return col_text[right[0]]
    return ""


def process_book(book: str):
    raw_dir   = os.path.join(RAW_BASE, book)
    patch_dir = os.path.join(PATCH_BASE, book)
    test_dir  = os.path.join(TEST_BASE, book)
    os.makedirs(test_dir, exist_ok=True)

    # Load nhãn gốc đã có
    orig_lbl_path = os.path.join(patch_dir, "labels.txt")
    labeled = {}
    if os.path.exists(orig_lbl_path):
        for line in open(orig_lbl_path, encoding="utf-8"):
            if "|" in line:
                fname, lbl = line.strip().split("|", 1)
                labeled[fname] = lbl

    # Load toàn bộ JSON → page_col_text
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

    # Gán nhãn ước lượng cho patch chưa có nhãn
    estimated: dict[str, str] = {}
    skipped = 0

    for fname in sorted(os.listdir(patch_dir)):
        if not fname.endswith(".jpg"):
            continue
        if fname in labeled:
            continue   # đã có nhãn gốc → bỏ qua

        parts = fname.rsplit("_", 1)
        if len(parts) != 2:
            continue
        page_name = parts[0]
        try:
            patch_idx = int(parts[1].replace(".jpg", ""))
        except:
            continue

        col_needed = patch_idx + 1
        ct = page_col_text.get(page_name, {})

        if not ct:
            skipped += 1
            continue

        if col_needed in ct:
            # Cột có sẵn (trường hợp này không nên xảy ra vì đã gán ở bước 1)
            estimated[fname] = ct[col_needed]
        else:
            # Cột bị thiếu → lấy text cột gần nhất
            est = nearest_col_text(ct, col_needed)
            if est:
                estimated[fname] = est
            else:
                skipped += 1

    # Ghi kết quả TEST (chỉ nhãn ước lượng, không có nhãn gốc)
    out_path = os.path.join(test_dir, "labels_estimated.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        for fname, lbl in sorted(estimated.items()):
            f.write(f"{fname}|{lbl}\n")

    # Ghi file kết hợp (gốc + ước lượng) để dùng thử
    combined_path = os.path.join(test_dir, "labels_combined.txt")
    combined = {**labeled, **estimated}
    with open(combined_path, "w", encoding="utf-8") as f:
        for fname, lbl in sorted(combined.items()):
            f.write(f"{fname}|{lbl}\n")

    print(f"{book}:")
    print(f"  Nhan goc:      {len(labeled)}")
    print(f"  Uoc luong moi: {len(estimated)}")
    print(f"  Bo qua:        {skipped}")
    print(f"  Ket hop:       {len(combined)}")
    print(f"  Luu tai:       {test_dir}")
    print()
    return len(estimated)


def main():
    print("=== Gán nhãn ước lượng DVSKTT → THƯ MỤC TEST ===")
    print(f"Kết quả lưu tại: {TEST_BASE}")
    print("KHÔNG ghi đè labels.txt gốc\n")

    total = 0
    for book in BOOKS:
        total += process_book(book)

    print(f"Tổng nhãn ước lượng mới: {total}")
    print()

    # Thống kê tổng
    print("=== Thống kê nếu dùng combined ===")
    grand = 0
    for book in BOOKS:
        path = os.path.join(TEST_BASE, book, "labels_combined.txt")
        if os.path.exists(path):
            n = sum(1 for l in open(path, encoding="utf-8") if "|" in l)
            grand += n
            print(f"  {book}: {n}")

    # Goc poetry
    for book in ["Luc Van Tien", "Tale of Kieu 1866", "Tale of Kieu 1871", "Tale of Kieu 1872"]:
        lbl = os.path.join(PATCH_BASE, book, "labels.txt")
        n = sum(1 for l in open(lbl, encoding="utf-8") if "|" in l)
        grand += n
        print(f"  {book}: {n}")

    ref = sum(1 for l in open("data/reference_chars/labels.txt", encoding="utf-8") if "|" in l)
    grand += ref
    print(f"  reference_chars: {ref}")
    print(f"\n  TONG (neu dung estimated): {grand}")


if __name__ == "__main__":
    main()
