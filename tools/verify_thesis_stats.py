"""Xác minh các con số thống kê trong Chương 4 luận văn."""
import os, sys, re, collections
sys.stdout.reconfigure(encoding='utf-8')

PATCH_BASE = "data/archive/Patches"

# ============================================================
# 1. Đếm tổng patches và pages (đã biết, kiểm tra lại)
# ============================================================
print("=" * 60)
print("1. THONG KE TRANG VA PATCH")
print("=" * 60)
total_patches = 0
book_patch_counts = {}
for book in sorted(os.listdir(PATCH_BASE)):
    book_dir = os.path.join(PATCH_BASE, book)
    if not os.path.isdir(book_dir):
        continue
    imgs = [f for f in os.listdir(book_dir) if f.endswith(".jpg")]
    book_patch_counts[book] = len(imgs)
    total_patches += len(imgs)
print(f"Tong patches: {total_patches}  (luan van ghi: 38.318)")

# ============================================================
# 2. Thống kê từ vựng từ labels.txt
# ============================================================
print()
print("=" * 60)
print("2. THONG KE TU VUNG (vocab)")
print("=" * 60)

char_freq = collections.Counter()

for book in sorted(os.listdir(PATCH_BASE)):
    labels_path = os.path.join(PATCH_BASE, book, "labels.txt")
    if not os.path.exists(labels_path):
        continue
    with open(labels_path, encoding="utf-8") as f:
        for line in f:
            if "|" not in line:
                continue
            label = line.strip().split("|", 1)[1]
            # Chỉ đếm ký tự Hán Nôm (Unicode CJK)
            for ch in label:
                cp = ord(ch)
                # CJK Unified + Extensions + Compatibility + Radicals + Nom range
                if (0x4E00 <= cp <= 0x9FFF or
                    0x3400 <= cp <= 0x4DBF or
                    0x20000 <= cp <= 0x2A6DF or
                    0x2A700 <= cp <= 0x2CEAF or
                    0xF900 <= cp <= 0xFAFF or
                    0xE0000 <= cp <= 0xEFFFF):
                    char_freq[ch] += 1

print(f"So ky tu Han Nom khac nhau: {len(char_freq)}  (luan van ghi: 7.509)")
print(f"Tong lan xuat hien         : {sum(char_freq.values())}  (luan van ghi: 459.547)")

# Phân bố theo khoảng tần suất
bands = [
    ("1",         lambda n: n == 1),
    ("2-5",       lambda n: 2 <= n <= 5),
    ("6-10",      lambda n: 6 <= n <= 10),
    ("11-20",     lambda n: 11 <= n <= 20),
    ("21-50",     lambda n: 21 <= n <= 50),
    ("51-100",    lambda n: 51 <= n <= 100),
    (">100",      lambda n: n > 100),
]
print()
print(f"  {'Khoang':>8}  {'So ky tu':>10}  {'Tong xuat hien':>16}  {'Luan van ghi':>30}")
print("  " + "-" * 70)

thesis_bands = [
    ("1",     1621, 1621),
    ("2-5",   1875, 5673),
    ("6-10",   856, 6560),
    ("11-20",  766, 11291),
    ("21-50",  894, 29561),
    ("51-100", 567, 40512),
    (">100",   930, 364374),
]
for (label, cond), (_, tv_cnt, tv_total) in zip(bands, thesis_bands):
    chars = {ch for ch, n in char_freq.items() if cond(n)}
    total = sum(char_freq[ch] for ch in chars)
    match_cnt   = "✓" if abs(len(chars) - tv_cnt)   <= 5 else f"✗ (gap {len(chars)-tv_cnt:+})"
    match_total = "✓" if abs(total - tv_total) <= 50 else f"✗ (gap {total-tv_total:+})"
    print(f"  {label:>8}  {len(chars):>10} {match_cnt:<15}  {total:>16} {match_total:<20}  (TV: {tv_cnt}, {tv_total})")

# ============================================================
# 3. Kiểm tra vocab.txt hiện có
# ============================================================
print()
print("=" * 60)
print("3. VOCAB.TXT HIEN CO")
print("=" * 60)
vocab_path = "assets/vocab.txt"
with open(vocab_path, encoding="utf-8") as f:
    vocab_chars = set(line.strip() for line in f if line.strip())
print(f"So ky tu trong vocab.txt  : {len(vocab_chars)}  (luan van ghi: 7.509)")
print(f"So ky tu trong labels     : {len(char_freq)}")
in_labels_not_vocab = set(char_freq.keys()) - vocab_chars
in_vocab_not_labels = vocab_chars - set(char_freq.keys())
print(f"Co trong labels, khong co trong vocab: {len(in_labels_not_vocab)}")
print(f"Co trong vocab, khong co trong labels: {len(in_vocab_not_labels)}")
