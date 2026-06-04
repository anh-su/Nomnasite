"""Kiểm tra tên trang (từ URL) trong từng file JSON so với tên patch thực tế."""
import json, os, re, sys
sys.stdout.reconfigure(encoding='utf-8')

RAW_BASE   = "data/archive/Raw"
PATCH_BASE = "data/archive/Patches"

DVSKTT_BOOKS = [
    "DVSKTT-1 Quyen thu",
    "DVSKTT-2 Ngoai ky toan thu",
    "DVSKTT-3 Ban ky toan thu",
    "DVSKTT-4 Ban ky thuc luc",
    "DVSKTT-5 Ban ky tuc bien",
]

for book in DVSKTT_BOOKS:
    raw_dir   = os.path.join(RAW_BASE, book)
    patch_dir = os.path.join(PATCH_BASE, book)
    if not os.path.isdir(raw_dir): continue

    # Lay tat ca patch page names
    patch_pages = set()
    for f in os.listdir(patch_dir):
        if f.endswith(".jpg"):
            patch_pages.add(f.rsplit("_", 1)[0])

    print(f"\n{'='*60}")
    print(f"SACH: {book}")
    print(f"  Patch pages: {len(patch_pages)} (vi du: {sorted(patch_pages)[:2]})")

    json_files = sorted(f for f in os.listdir(raw_dir) if f.endswith(".json"))
    for jf in json_files:
        data = json.load(open(os.path.join(raw_dir, jf), encoding="utf-8"))
        if not isinstance(data, list) or not data:
            continue
        # Lay page names tu entries
        json_pages_in_file = set()
        has_col_marker = False
        for entry in data:
            url = entry.get("url", "")
            page = os.path.splitext(os.path.basename(url))[0]
            json_pages_in_file.add(page)
            text = entry.get("text", "")
            if re.search(r'\.\s*\[(\w+)\*(\d+)\*(\d+)\]', text):
                has_col_marker = True

        matched = json_pages_in_file & patch_pages
        url_sample = sorted(json_pages_in_file)[0] if json_pages_in_file else "?"
        print(f"  [{jf:<35}] pages={len(json_pages_in_file):4}  khop-patch={len(matched):4}"
              f"  col-marker={'Y' if has_col_marker else 'N'}"
              f"  vi-du={url_sample}")
