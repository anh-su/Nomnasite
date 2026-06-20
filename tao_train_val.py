import os
import random

PATCH_DIR = "data/archive/Patches"

TRAIN_FILE = "assets/train.txt"
VAL_FILE = "assets/val.txt"

all_samples = []

print("Đang quét labels.txt...")

for root, dirs, files in os.walk(PATCH_DIR):

    if "labels.txt" in files:

        label_file = os.path.join(root, "labels.txt")

        with open(label_file, "r", encoding="utf-8") as f:

            for line in f:

                line = line.strip()

                if "|" not in line:
                    continue

                img_name, label = line.split("|", 1)

                try:
                    label = label.encode("latin1").decode("utf-8")
                except:
                    pass    

                img_path = os.path.join(root, img_name)

                if not os.path.exists(img_path):
                    continue

                img_path = img_path.replace("\\", "/")

                all_samples.append(
                    (img_path, label)
                )

print(f"Tổng mẫu: {len(all_samples)}")

# Trộn dữ liệu
random.seed(42)
random.shuffle(all_samples)

# Chia 80/20
split_idx = int(len(all_samples) * 0.8)

train_samples = all_samples[:split_idx]
val_samples = all_samples[split_idx:]

# Lưu train
with open(TRAIN_FILE, "w", encoding="utf-8") as f:

    for img_path, label in train_samples:

        f.write(
            f"{img_path}|{label}\n"
        )

# Lưu val
with open(VAL_FILE, "w", encoding="utf-8") as f:

    for img_path, label in val_samples:

        f.write(
            f"{img_path}|{label}\n"
        )

print("\n===== THỐNG KÊ =====")
print("Train:", len(train_samples))
print("Val  :", len(val_samples))
print("Đã lưu:")
print(TRAIN_FILE)
print(VAL_FILE)