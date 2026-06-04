"""
Đánh giá char_acc và CER của CRNN.h5 (base) và CRNN_retrained.h5 (retrained).
Chạy: python tools/evaluate_crnn.py
"""
import os, sys, random, collections
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
sys.stdout.reconfigure(encoding="utf-8")

import numpy as np
import tensorflow as tf
import cv2
tf.get_logger().setLevel("ERROR")

# ─── thêm root vào sys.path ────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from crnn import CRNN

PATCH_BASE  = os.path.join(ROOT, "data", "archive", "Patches")
ASSET_BASE  = os.path.join(ROOT, "assets")
SAMPLE_SIZE = 500   # mỗi model đánh giá trên N patch ngẫu nhiên
SEED        = 42
MAX_LABEL   = 24    # CRNN chỉ decode tối đa 24 ký tự

# Chỉ dùng sách thơ — nhãn per-column đúng (~7 ký tự/cột)
# DVSKTT có nhãn ~34 ký tự (nhãn cả hàng, không phải cột đơn) → bỏ qua
POETRY_BOOKS = [
    "Tale of Kieu 1866",
    "Tale of Kieu 1871",
    "Tale of Kieu 1872",
    "Luc Van Tien",
]


# ─── Load (image_path, label) từ các sách thơ ─────────────────
def load_all_samples():
    samples = []
    for book in POETRY_BOOKS:
        book_dir = os.path.join(PATCH_BASE, book)
        lbl_path = os.path.join(book_dir, "labels.txt")
        if not os.path.isdir(book_dir) or not os.path.exists(lbl_path):
            continue
        with open(lbl_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if "|" not in line:
                    continue
                fname, label = line.split("|", 1)
                label = label.strip()
                img_path = os.path.join(book_dir, fname)
                if os.path.exists(img_path) and label and len(label) <= MAX_LABEL:
                    samples.append((img_path, label))
    return samples


# ─── Metrics ──────────────────────────────────────────────────
def edit_distance(s1, s2):
    """Levenshtein distance between two strings."""
    m, n = len(s1), len(s2)
    dp = list(range(n + 1))
    for i in range(1, m + 1):
        prev = dp[0]
        dp[0] = i
        for j in range(1, n + 1):
            temp = dp[j]
            if s1[i-1] == s2[j-1]:
                dp[j] = prev
            else:
                dp[j] = 1 + min(prev, dp[j], dp[j-1])
            prev = temp
    return dp[n]


def compute_metrics(predictions, ground_truths):
    """Tính char_acc và CER."""
    total_chars  = 0
    correct_chars = 0
    total_edit   = 0
    total_gt_len = 0

    for pred, gt in zip(predictions, ground_truths):
        gt_len = len(gt)
        if gt_len == 0:
            continue
        # Char accuracy: từng ký tự tại vị trí tương ứng
        min_len = min(len(pred), gt_len)
        correct_chars += sum(p == g for p, g in zip(pred, gt))
        total_chars   += gt_len

        # CER
        total_edit   += edit_distance(pred, gt)
        total_gt_len += gt_len

    char_acc = correct_chars / total_chars if total_chars > 0 else 0
    cer      = total_edit   / total_gt_len if total_gt_len > 0 else 0
    return char_acc, cer


# ─── Đánh giá một model ───────────────────────────────────────
def evaluate_model(model_path, samples, label=""):
    print(f"\n{'='*55}")
    print(f"  Model: {label}")
    print(f"  Weights: {os.path.basename(model_path)}")
    print(f"  Samples: {len(samples)}")
    print(f"{'='*55}")

    crnn = CRNN()
    crnn.model.load_weights(model_path)

    predictions = []
    ground_truths = []
    errors = 0

    for i, (img_path, gt) in enumerate(samples):
        if (i + 1) % 100 == 0:
            print(f"  [{i+1}/{len(samples)}] ...")
        try:
            import cv2
            buf = np.fromfile(img_path, dtype=np.uint8)
            img = cv2.imdecode(buf, cv2.IMREAD_COLOR)
            if img is None:
                errors += 1
                continue
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            # Gọi trực tiếp bỏ qua st.cache_data để tránh cache trả kết quả sai trong batch
            image  = crnn.process_image(img_rgb)
            ptok   = crnn.model.predict(tf.expand_dims(image, 0), verbose=0)
            pred   = crnn.tokens2texts(ptok)[0]
            predictions.append(pred)
            ground_truths.append(gt)
        except Exception:
            errors += 1

    print(f"  Lỗi đọc ảnh: {errors}")
    char_acc, cer = compute_metrics(predictions, ground_truths)

    print(f"\n  ┌─────────────────────────────────┐")
    print(f"  │  char_acc : {char_acc*100:6.2f}%             │")
    print(f"  │  CER      : {cer*100:6.2f}%             │")
    print(f"  └─────────────────────────────────┘")

    # Xem 5 ví dụ ngẫu nhiên
    print(f"\n  Vi du (GT vs Pred):")
    pairs = list(zip(ground_truths, predictions))
    random.shuffle(pairs)
    for gt_ex, pred_ex in pairs[:5]:
        match = "OK" if pred_ex == gt_ex else f"SAI (edit={edit_distance(pred_ex,gt_ex)})"
        # encode sang ASCII-safe để tránh lỗi console Windows
        gt_safe   = gt_ex[:20].encode("unicode_escape").decode("ascii")
        pred_safe = pred_ex[:20].encode("unicode_escape").decode("ascii")
        print(f"    GT  : {gt_safe}")
        print(f"    Pred: {pred_safe}  [{match}]")
        print()

    return char_acc, cer


# ─── Main ─────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Đang tải dữ liệu...")
    all_samples = load_all_samples()
    print(f"Tổng số mẫu hợp lệ: {len(all_samples)}")

    random.seed(SEED)
    sample = random.sample(all_samples, min(SAMPLE_SIZE, len(all_samples)))

    results = {}

    # Đánh giá CRNN.h5 (base / fine-tuned)
    base_path = os.path.join(ASSET_BASE, "CRNN.h5")
    if os.path.exists(base_path):
        acc, cer = evaluate_model(base_path, sample, label="CRNN.h5  (Fine-tuning)")
        results["CRNN.h5"] = (acc, cer)

    # Đánh giá CRNN_retrained.h5
    retrain_path = os.path.join(ASSET_BASE, "CRNN_retrained.h5")
    if os.path.exists(retrain_path):
        acc, cer = evaluate_model(retrain_path, sample, label="CRNN_retrained.h5  (Retraining)")
        results["CRNN_retrained.h5"] = (acc, cer)

    # Tổng kết
    print("\n" + "="*55)
    print("  TỔNG KẾT SO SÁNH")
    print("="*55)
    print(f"  {'Model':<25} {'char_acc':>10} {'CER':>10}")
    print(f"  {'-'*47}")
    for name, (acc, cer) in results.items():
        print(f"  {name:<25} {acc*100:>9.2f}% {cer*100:>9.2f}%")
    print()
    print("  (Luận văn: Fine-tuning = 83.25% / 16.17%,  Retraining = 84.73% / 15.08%)")
    print("="*55)
