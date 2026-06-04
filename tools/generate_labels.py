"""
Tạo file labels.txt cho từng book trong data/archive/Patches/
Format: image_name|nom_label
Chỉ xử lý các book có số patch ≈ số label (chênh lệch < 50)
"""
import os
import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

ARCHIVE_PATCHES = "data/archive/Patches"
ARCHIVE_RAW = "data/archive/Raw"


def natural_sort_key(filename):
    """Sort page001a_2.jpg trước page001a_10.jpg"""
    match = re.match(r'page([^_]+)_(\d+)\.jpg', filename)
    if match:
        page_id = match.group(1)
        col_idx = int(match.group(2))
        # tách phần số và chữ trong page_id để sort đúng
        num_part = re.sub(r'[^0-9]', '', page_id)
        alpha_part = re.sub(r'[0-9]', '', page_id)
        return (int(num_part) if num_part else 0, alpha_part, col_idx)
    return (0, filename, 0)


def load_nom_labels(trans_path):
    labels = []
    with open(trans_path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or '\t' not in line:
                continue
            nom = line.split('\t')[0].strip()
            if nom:
                labels.append(nom)
    return labels


def generate_for_book(book_name):
    patch_dir = os.path.join(ARCHIVE_PATCHES, book_name)
    trans_path = os.path.join(ARCHIVE_RAW, book_name, "translation.txt")

    if not os.path.exists(trans_path):
        print(f"  Bỏ qua {book_name}: không có translation.txt")
        return 0

    patches = sorted(
        [f for f in os.listdir(patch_dir) if f.endswith('.jpg')],
        key=natural_sort_key
    )
    labels = load_nom_labels(trans_path)

    diff = abs(len(patches) - len(labels))
    if diff > 50:
        print(f"  Bỏ qua {book_name}: {len(patches)} patches vs {len(labels)} labels (chênh {diff})")
        return 0

    # dùng min để tránh index out of range
    count = min(len(patches), len(labels))
    output_path = os.path.join(patch_dir, "labels.txt")

    with open(output_path, 'w', encoding='utf-8') as f:
        for i in range(count):
            f.write(f"{patches[i]}|{labels[i]}\n")

    print(f"  OK {book_name}: {count} mẫu → {output_path}")
    return count


def main():
    if not os.path.exists(ARCHIVE_PATCHES):
        print("Không tìm thấy data/archive/Patches/")
        sys.exit(1)

    total = 0
    for book in sorted(os.listdir(ARCHIVE_PATCHES)):
        total += generate_for_book(book)

    print(f"\nTổng cộng: {total} mẫu label được tạo")


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    main()
