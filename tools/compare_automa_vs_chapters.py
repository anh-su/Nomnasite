"""So sánh coverage (page, col) giữa automa.json và các file chapter."""
import json, os, re, sys
sys.stdout.reconfigure(encoding='utf-8')

RAW_BASE   = "data/archive/Raw"
PATCH_BASE = "data/archive/Patches"

BOOKS = [
    "DVSKTT-1 Quyen thu",
    "DVSKTT-2 Ngoai ky toan thu",
    "DVSKTT-3 Ban ky toan thu",
    "DVSKTT-4 Ban ky thuc luc",
    "DVSKTT-5 Ban ky tuc bien",
]


def get_page_col_set(filepath):
    """Trả về set of (page, col) từ một file JSON."""
    result = set()
    data = json.load(open(filepath, encoding="utf-8"))
    if not isinstance(data, list):
        return result
    for entry in data:
        url  = entry.get("url", "")
        page = os.path.splitext(os.path.basename(url))[0]
        for line in entry.get("text", "").split("\n"):
            m = re.search(r'\.\s*\[(\w+)\*(\d+)\*(\d+)\]', line)
            if m:
                col = int(m.group(2))
                result.add((page, col))
    return result


for book in BOOKS:
    raw_dir   = os.path.join(RAW_BASE, book)
    patch_dir = os.path.join(PATCH_BASE, book)

    # Tap hop (page, col) can co tu patches
    needed = set()
    for f in os.listdir(patch_dir):
        if not f.endswith(".jpg"):
            continue
        parts = f.rsplit("_", 1)
        if len(parts) != 2:
            continue
        page = parts[0]
        try:
            idx = int(parts[1].replace(".jpg", ""))
            needed.add((page, idx + 1))
        except ValueError:
            pass

    # Coverage tu automa.json
    automa_path = os.path.join(raw_dir, "automa.json")
    automa_cols = get_page_col_set(automa_path) if os.path.exists(automa_path) else set()

    # Coverage tu cac chapter files (tat ca .json tru automa.json)
    chapter_cols = set()
    chapter_files = [f for f in os.listdir(raw_dir)
                     if f.endswith(".json") and f != "automa.json"]
    for jf in chapter_files:
        chapter_cols |= get_page_col_set(os.path.join(raw_dir, jf))

    # Coverage khi gop ca hai
    combined_cols = automa_cols | chapter_cols

    # Khop voi patches
    automa_match   = automa_cols   & needed
    chapter_match  = chapter_cols  & needed
    combined_match = combined_cols & needed

    only_in_automa  = (automa_cols   - chapter_cols) & needed
    only_in_chapter = (chapter_cols  - automa_cols)  & needed

    print(f"\n{'='*60}")
    print(f"SACH: {book}")
    print(f"  Tong patches can label : {len(needed)}")
    print(f"  automa.json   (page,col): {len(automa_cols):5}  -> khop patches: {len(automa_match)}")
    print(f"  chapter files (page,col): {len(chapter_cols):5}  -> khop patches: {len(chapter_match)}")
    print(f"  KET HOP       (page,col): {len(combined_cols):5}  -> khop patches: {len(combined_match)}")
    print(f"  Chi co trong automa   (+): {len(only_in_automa)}")
    print(f"  Chi co trong chapter  (+): {len(only_in_chapter)}")
    print(f"  Van thieu (chua the label): {len(needed) - len(combined_match)}")
