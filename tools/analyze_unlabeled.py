"""Phân tích 12.365 patch chưa có nhãn trong DVSKTT."""
import json, os, re

RAW_BASE   = "data/archive/Raw"
PATCH_BASE = "data/archive/Patches"

BOOKS = [
    "DVSKTT-1 Quyen thu",
    "DVSKTT-2 Ngoai ky toan thu",
    "DVSKTT-3 Ban ky toan thu",
    "DVSKTT-4 Ban ky thuc luc",
    "DVSKTT-5 Ban ky tuc bien",
]

total_no_json = 0
total_col_gap  = 0

for book in BOOKS:
    raw_dir   = os.path.join(RAW_BASE, book)
    patch_dir = os.path.join(PATCH_BASE, book)
    lbl_path  = os.path.join(patch_dir, "labels.txt")

    # Load nhãn đã có
    labeled_patches = set()
    if os.path.exists(lbl_path):
        for line in open(lbl_path, encoding="utf-8"):
            if "|" in line:
                labeled_patches.add(line.split("|")[0].strip())

    # Load pages có trong JSON
    json_page_cols: dict[str, set] = {}  # page → set of col numbers
    for jf in sorted(f for f in os.listdir(raw_dir) if f.endswith(".json")):
        data = json.load(open(os.path.join(raw_dir, jf), encoding="utf-8"))
        for entry in data:
            url  = entry.get("url", "")
            page = os.path.splitext(os.path.basename(url))[0]
            cols = set()
            for line in entry.get("text", "").split("\n"):
                m = re.search(r"\.\s*\[(\w+)\*(\d+)\*(\d+)\]", line)
                if m:
                    cols.add(int(m.group(2)))
            json_page_cols[page] = json_page_cols.get(page, set()) | cols

    # Phân tích patch chưa có nhãn
    n_no_json = 0  # patch thuộc trang không có trong JSON
    n_col_gap  = 0  # patch thuộc trang có JSON nhưng col bị thiếu

    for fname in sorted(os.listdir(patch_dir)):
        if not fname.endswith(".jpg"):
            continue
        if fname in labeled_patches:
            continue
        # Lấy page name và col index
        parts = fname.rsplit("_", 1)
        if len(parts) != 2:
            continue
        page_name = parts[0]
        try:
            patch_idx = int(parts[1].replace(".jpg", ""))
        except:
            continue

        if page_name not in json_page_cols:
            n_no_json += 1
        else:
            # Patch idx = col - 1 → col = patch_idx + 1
            col_needed = patch_idx + 1
            if col_needed not in json_page_cols[page_name]:
                n_col_gap += 1

    total_no_json += n_no_json
    total_col_gap  += n_col_gap
    print(f"{book}:")
    print(f"  Trang không có trong JSON: {n_no_json} patch")
    print(f"  Cột bị thiếu trong JSON:   {n_col_gap} patch")
    print()

print(f"Tổng trang không có JSON: {total_no_json}")
print(f"Tổng cột bị thiếu:        {total_col_gap}")
print(f"Tổng chưa nhãn:           {total_no_json + total_col_gap}")
