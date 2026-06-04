"""
Tính vocab từ TOÀN BỘ labels hiện có (tất cả patches có nhãn),
so sánh với số liệu trong luận văn.
"""
import os, sys, collections, re
sys.stdout.reconfigure(encoding='utf-8')

PATCH_BASE = "data/archive/Patches"

# Regex lọc ký tự Hán Nôm (CJK + extensions + private use Nom)
def is_han_nom(ch):
    cp = ord(ch)
    return (
        0x4E00  <= cp <= 0x9FFF  or   # CJK Unified
        0x3400  <= cp <= 0x4DBF  or   # CJK Ext-A
        0x20000 <= cp <= 0x2A6DF or   # CJK Ext-B
        0x2A700 <= cp <= 0x2CEAF or   # CJK Ext-C/D/E/F
        0xF900  <= cp <= 0xFAFF  or   # CJK Compat Ideographs
        0xE0000 <= cp <= 0xEFFFF or   # Tags
        cp >= 0x100000                # Supplementary (Nom range)
    )

char_freq = collections.Counter()
total_patches_labeled = 0

for book in sorted(os.listdir(PATCH_BASE)):
    lbl_path = os.path.join(PATCH_BASE, book, "labels.txt")
    if not os.path.exists(lbl_path):
        continue
    with open(lbl_path, encoding='utf-8') as f:
        for line in f:
            if '|' not in line:
                continue
            label = line.strip().split('|', 1)[1]
            total_patches_labeled += 1
            for ch in label:
                if is_han_nom(ch):
                    char_freq[ch] += 1

total_chars   = sum(char_freq.values())
unique_chars  = len(char_freq)
avg_per_patch = total_chars / total_patches_labeled if total_patches_labeled else 0

print("=" * 60)
print("KET QUA THONG KE VOCAB TU TOAN BO LABELS HIEN TAI")
print("=" * 60)
print(f"Tong patches co nhan       : {total_patches_labeled:,}")
print(f"So ky tu Han Nom khac nhau : {unique_chars:,}  (LV ghi: 7.509)")
print(f"Tong lan xuat hien         : {total_chars:,}  (LV ghi: 459.547)")
print(f"Trung binh ky tu/nhan      : {avg_per_patch:.1f}")
print()

# Phân bố theo khoảng tần suất
thesis = [
    ("1",      1621, 1621),
    ("2–5",    1875, 5673),
    ("6–10",    856, 6560),
    ("11–20",   766, 11291),
    ("21–50",   894, 29561),
    ("51–100",  567, 40512),
    (">100",    930, 364374),
]
conds = [
    lambda n: n == 1,
    lambda n: 2 <= n <= 5,
    lambda n: 6 <= n <= 10,
    lambda n: 11 <= n <= 20,
    lambda n: 21 <= n <= 50,
    lambda n: 51 <= n <= 100,
    lambda n: n > 100,
]

print(f"{'Khoang':>8}  {'Thuc te':>10}  {'LV ghi':>8}  {'Chenh':>8}  |  {'Tong xh':>10}  {'LV ghi':>10}  {'Chenh':>8}")
print("-" * 82)
total_actual_chars = total_actual_cnt = 0
for (lbl, tv_cnt, tv_total), cond in zip(thesis, conds):
    chars = {ch for ch, n in char_freq.items() if cond(n)}
    total = sum(char_freq[ch] for ch in chars)
    d_cnt = len(chars) - tv_cnt
    d_tot = total - tv_total
    print(f"{lbl:>8}  {len(chars):>10,}  {tv_cnt:>8,}  {d_cnt:>+8,}  |  {total:>10,}  {tv_total:>10,}  {d_tot:>+8,}")
    total_actual_chars += len(chars)
    total_actual_cnt   += total

print("-" * 82)
print(f"{'TONG':>8}  {total_actual_chars:>10,}  {'7.509':>8}  {total_actual_chars-7509:>+8,}  |  {total_actual_cnt:>10,}  {'459.547':>10}  {total_actual_cnt-459547:>+8,}")

print()
print("=== VOCAB.TXT HIEN CO ===")
with open("assets/vocab.txt", encoding="utf-8") as f:
    vocab_set = set(line.strip() for line in f if line.strip())
print(f"So ky tu trong vocab.txt : {len(vocab_set):,}  (LV ghi: 7.509)")
print(f"Co trong labels, thieu trong vocab: {len(set(char_freq.keys()) - vocab_set)}")
print(f"Co trong vocab, khong co trong labels: {len(vocab_set - set(char_freq.keys()))}")
