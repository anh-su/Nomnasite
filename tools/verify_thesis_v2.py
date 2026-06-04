"""
Xác minh con số luận văn Chương 4.
Chỉ lấy nhãn CHÍNH XÁC (khớp cột trong JSON) cho DVSKTT,
cộng thêm toàn bộ nhãn thơ (Kieu, Luc Van Tien) và reference_chars.
"""
import os, sys, re, json, collections
sys.stdout.reconfigure(encoding='utf-8')

RAW_BASE   = "data/archive/Raw"
PATCH_BASE = "data/archive/Patches"

POETRY_BOOKS = ["Luc Van Tien", "Tale of Kieu 1866", "Tale of Kieu 1871", "Tale of Kieu 1872"]
DVSKTT_BOOKS = [
    "DVSKTT-1 Quyen thu",
    "DVSKTT-2 Ngoai ky toan thu",
    "DVSKTT-3 Ban ky toan thu",
    "DVSKTT-4 Ban ky thuc luc",
    "DVSKTT-5 Ban ky tuc bien",
]


def extract_col_text(text):
    col_map = {}
    for line in text.split("\n"):
        m = re.search(r'\.\s*\[(\w+)\*(\d+)\*(\d+)\]', line)
        if not m:
            continue
        col = int(m.group(2))
        row = int(m.group(3))
        clean = re.sub(r'\s*\.\s*\[[^\]]+\]', '', line)
        clean = re.sub(r'\s+', '', clean).strip()
        if clean:
            col_map.setdefault(col, []).append((row, clean))
    return {col: "".join(t for _, t in sorted(entries))
            for col, entries in col_map.items()}


def load_exact_dvsktt_labels():
    """Lấy đúng các nhãn khớp cột trong JSON (nhãn gốc, không ước lượng)."""
    labels = {}
    for book in DVSKTT_BOOKS:
        raw_dir   = os.path.join(RAW_BASE, book)
        patch_dir = os.path.join(PATCH_BASE, book)
        page_col_text = {}
        for jf in sorted(f for f in os.listdir(raw_dir) if f.endswith(".json")):
            data = json.load(open(os.path.join(raw_dir, jf), encoding="utf-8"))
            for entry in data:
                url  = entry.get("url", "")
                page = os.path.splitext(os.path.basename(url))[0]
                ct   = extract_col_text(entry.get("text", ""))
                if page not in page_col_text:
                    page_col_text[page] = {}
                page_col_text[page].update(ct)
        for fname in os.listdir(patch_dir):
            if not fname.endswith(".jpg"):
                continue
            parts = fname.rsplit("_", 1)
            if len(parts) != 2:
                continue
            page = parts[0]
            try:
                idx = int(parts[1].replace(".jpg", ""))
            except ValueError:
                continue
            col = idx + 1
            ct = page_col_text.get(page, {})
            if col in ct:
                labels[fname] = ct[col]
    return labels


def load_labels_file(img_dir, lbl_path):
    result = {}
    if not os.path.exists(lbl_path):
        return result
    with open(lbl_path, encoding="utf-8") as f:
        for line in f:
            if "|" not in line:
                continue
            fname, label = line.strip().split("|", 1)
            img_path = os.path.join(img_dir, fname)
            if os.path.exists(img_path):
                result[fname] = label
    return result


# ── Thu thập nhãn ────────────────────────────────────────────
all_labels = {}

# 1. Poetry books (100% chính xác)
for book in POETRY_BOOKS:
    book_dir = os.path.join(PATCH_BASE, book)
    d = load_labels_file(book_dir, os.path.join(book_dir, "labels.txt"))
    all_labels.update(d)
print(f"Sau khi load tho         : {len(all_labels):6} nhan")

# 2. DVSKTT - chỉ nhãn chính xác
dvsktt_exact = load_exact_dvsktt_labels()
all_labels.update(dvsktt_exact)
print(f"Sau khi them DVSKTT exact: {len(all_labels):6} nhan")

# 3. Reference chars
ref_d = load_labels_file("data/reference_chars/images",
                         "data/reference_chars/labels.txt")
all_labels.update(ref_d)
print(f"Sau khi them reference   : {len(all_labels):6} nhan")

# ── Thống kê ký tự ────────────────────────────────────────────
def is_han_nom(ch):
    cp = ord(ch)
    return (0x4E00 <= cp <= 0x9FFF or
            0x3400 <= cp <= 0x4DBF or
            0x20000 <= cp <= 0x2A6DF or
            0x2A700 <= cp <= 0x2CEAF or
            0xF900 <= cp <= 0xFAFF or
            0xE0000 <= cp <= 0xEFFFF or
            cp >= 0x100000)

char_freq = collections.Counter()
total_chars = 0
for label in all_labels.values():
    for ch in label:
        if is_han_nom(ch):
            char_freq[ch] += 1
            total_chars += 1

print()
print("=" * 65)
print("KIEM TRA THONG KE LUAN VAN")
print("=" * 65)
print(f"Tong nhan co trong tinh toan     : {len(all_labels)}")
print(f"  trong do DVSKTT exact          : {len(dvsktt_exact)}")
print()
print(f"So ky tu Han Nom khac nhau: {len(char_freq):5}  | LV ghi: 7.509  | {'✓' if abs(len(char_freq)-7509)<=30 else '✗ SAI'}")
print(f"Tong lan xuat hien        : {total_chars:6}  | LV ghi: 459.547  | {'✓' if abs(total_chars-459547)<=500 else '✗ SAI'}")

# Chiều dài trung bình
avg = total_chars / len(all_labels) if all_labels else 0
print(f"Trung binh ky tu/nhan     : {avg:5.1f}")

print()
print(f"{'Khoang':>8}  {'Thuc te':>8}  {'LV ghi':>8}  {'Ket qua'}")
print("-" * 45)
bands = [("1",1621),("2-5",1875),("6-10",856),("11-20",766),("21-50",894),("51-100",567),(">100",930)]
conds = [lambda n:n==1, lambda n:2<=n<=5, lambda n:6<=n<=10,
         lambda n:11<=n<=20, lambda n:21<=n<=50, lambda n:51<=n<=100, lambda n:n>100]
for (lbl, tv), cond in zip(bands, conds):
    actual = sum(1 for n in char_freq.values() if cond(n))
    ok = "✓" if abs(actual - tv) <= 10 else f"✗ ({actual:+d} vs {tv})"
    print(f"{lbl:>8}  {actual:>8}  {tv:>8}  {ok}")
print(f"{'TONG':>8}  {len(char_freq):>8}  {'7509':>8}")
