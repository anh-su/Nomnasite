import os, re, sys
sys.stdout.reconfigure(encoding='utf-8')

# Count pages
raw_root = 'data/archive/Raw'
total_pages = 0
book_pages = {}
for book in os.listdir(raw_root):
    book_path = os.path.join(raw_root, book)
    if not os.path.isdir(book_path):
        continue
    jsons = [f for f in os.listdir(book_path) if f.endswith('.json')]
    book_pages[book] = len(jsons)
    total_pages += len(jsons)

print('=== SO TRANG THEO SACH (Raw JSON) ===')
for book, cnt in sorted(book_pages.items()):
    print('  {:<38} {:>5} trang'.format(book, cnt))
print('  {:<38} {:>5} trang'.format('TONG', total_pages))

# Count patches and digit-containing labels
patches_root = 'data/archive/Patches'
total_patches = 0
digit_patches = 0
book_stats = {}
digit_re = re.compile(r'[0-9]')

for book in sorted(os.listdir(patches_root)):
    book_path = os.path.join(patches_root, book)
    labels_file = os.path.join(book_path, 'labels.txt')
    if not os.path.isfile(labels_file):
        continue
    with open(labels_file, encoding='utf-8') as f:
        lines = [l.strip() for l in f if l.strip()]
    book_total = 0
    book_digit = 0
    digit_examples = []
    for line in lines:
        parts = line.split('|')
        if len(parts) < 2:
            continue
        label = parts[1]
        book_total += 1
        if digit_re.search(label):
            book_digit += 1
            if len(digit_examples) < 2:
                digit_examples.append(parts[0] + ' -> ' + repr(label))
    book_stats[book] = (book_total, book_digit, digit_examples)
    total_patches += book_total
    digit_patches += book_digit

print()
print('=== THONG KE PATCH THEO SACH ===')
print('{:<38} {:>10} {:>13}  {}'.format('Sach', 'Tong patch', 'Patch co so', 'Vi du'))
print('-' * 100)
for book, (tot, dig, exs) in sorted(book_stats.items()):
    ex_str = '; '.join(exs) if exs else '-'
    print('{:<38} {:>10} {:>13}  {}'.format(book, tot, dig, ex_str))
print('-' * 100)
print('{:<38} {:>10} {:>13}'.format('TONG CONG', total_patches, digit_patches))
pct = digit_patches / total_patches * 100 if total_patches else 0
print('Ty le patch co ky tu so: {:.2f}%'.format(pct))
