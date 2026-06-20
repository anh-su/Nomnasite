
import os
import numpy as np
import tensorflow as tf

# ==============================
# GPU
# ==============================
for gpu in tf.config.list_physical_devices('GPU'):
    tf.config.experimental.set_memory_growth(gpu, True)

from crnn import CRNN

# ==============================
# Cấu hình
# ==============================
VAL_FILE = "assets/val.txt"
WEIGHTS = "assets/CRNN.h5"
MAX_LABEL_LEN = 24

# ==============================
# Load dữ liệu
# ==============================
def load_samples(txt_file):
    samples = []

    with open(txt_file, "r", encoding="utf-8") as f:

        for line in f:

            line = line.strip()

            if "|" not in line:
                continue

            img_path, label = line.split("|", 1)

            img_path = img_path.replace("\\", os.sep)

            if os.path.exists(img_path):
                samples.append((img_path, label))

    return samples


# ==============================
# CER
# ==============================
def cer_score(gt, pred):

    if len(gt) == 0:
        return 0.0 if len(pred) == 0 else 1.0

    m = len(gt)
    n = len(pred)

    dp = [[0]*(n+1) for _ in range(m+1)]

    for i in range(m+1):
        dp[i][0] = i

    for j in range(n+1):
        dp[0][j] = j

    for i in range(1, m+1):

        for j in range(1, n+1):

            if gt[i-1] == pred[j-1]:

                dp[i][j] = dp[i-1][j-1]

            else:

                dp[i][j] = 1 + min(
                    dp[i-1][j],
                    dp[i][j-1],
                    dp[i-1][j-1]
                )

    return dp[m][n] / m


# ==============================
# Precision Recall F1
# ==============================
def prf_chars(gt, pred):

    from collections import Counter

    gt_c = Counter(gt)
    pred_c = Counter(pred)

    tp = sum((gt_c & pred_c).values())

    fp = sum(pred_c.values()) - tp
    fn = sum(gt_c.values()) - tp

    precision = tp / (tp + fp) if (tp + fp) else 0
    recall = tp / (tp + fn) if (tp + fn) else 0

    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall)
        else 0
    )

    return precision, recall, f1


# ==============================
# Load model
# ==============================
print("Loading model...")

crnn = CRNN()
crnn.model.load_weights(WEIGHTS)

print("Loaded:", WEIGHTS)

# ==============================
# Load val
# ==============================
val_samples = load_samples(VAL_FILE)

print("Val gốc:", len(val_samples))

val_samples = [
    (p, l)
    for p, l in val_samples
    if len(l) <= MAX_LABEL_LEN
]

print("Val sau lọc:", len(val_samples))

if len(val_samples) == 0:
    raise Exception("Không đọc được dữ liệu validation")

print("Ví dụ đầu tiên:")
print(val_samples[0])

val_paths = [x[0] for x in val_samples]
val_labels = [x[1] for x in val_samples]

# ==============================
# Evaluate
# ==============================
print("\nEvaluating...")

pred_texts = []
all_conf = []

for i, (path, gt) in enumerate(
    zip(val_paths, val_labels)
):

    try:

        raw = tf.io.read_file(path)

        raw = tf.image.decode_jpeg(
            raw,
            channels=3
        )

        raw = tf.cast(
            raw,
            tf.float32
        )

        image = crnn.process_image(raw)

        pred_tokens = crnn.model.predict(
            tf.expand_dims(image, axis=0),
            verbose=0
        )

        pred_text = crnn.tokens2texts(
            pred_tokens
        )[0]

        confidence = float(
            pred_tokens[0]
            .max(axis=-1)
            .mean()
        )

        pred_texts.append(pred_text)
        all_conf.append(confidence)

    except Exception as e:

        print("ERROR:", path)
        print(e)
        continue

    if (i + 1) % 500 == 0:

        print(
            f"{i+1}/{len(val_paths)} done..."
        )

# ==============================
# Metrics
# ==============================
cer_list = [
    cer_score(g, p)
    for g, p in zip(
        val_labels,
        pred_texts
    )
]

prf_list = [
    prf_chars(g, p)
    for g, p in zip(
        val_labels,
        pred_texts
    )
]

mean_cer = np.mean(cer_list)
mean_acc = 1 - mean_cer

mean_conf = np.mean(all_conf)

mean_p = np.mean(
    [x[0] for x in prf_list]
)

mean_r = np.mean(
    [x[1] for x in prf_list]
)

mean_f1 = np.mean(
    [x[2] for x in prf_list]
)

# ==============================
# Kết quả
# ==============================
print("\n" + "="*60)
print("KẾT QUẢ ĐÁNH GIÁ CRNN")
print("="*60)

print(
    f"Character Accuracy : "
    f"{mean_acc*100:.2f}%"
)

print(
    f"CER                : "
    f"{mean_cer*100:.2f}%"
)

print(
    f"Confidence Score   : "
    f"{mean_conf*100:.2f}%"
)

print(
    f"Precision          : "
    f"{mean_p:.4f}"
)

print(
    f"Recall             : "
    f"{mean_r:.4f}"
)

print(
    f"F1-score           : "
    f"{mean_f1:.4f}"
)

print(
    f"Số mẫu đánh giá    : "
    f"{len(pred_texts)}"
)

# ==============================
# Lưu file
# ==============================
os.makedirs(
    "eval",
    exist_ok=True
)

with open(
    "eval/results.txt",
    "w",
    encoding="utf-8"
) as f:

    f.write(
        f"Character Accuracy : {mean_acc*100:.2f}%\n"
    )

    f.write(
        f"CER : {mean_cer*100:.2f}%\n"
    )

    f.write(
        f"Confidence : {mean_conf*100:.2f}%\n"
    )

    f.write(
        f"Precision : {mean_p:.4f}\n"
    )

    f.write(
        f"Recall : {mean_r:.4f}\n"
    )

    f.write(
        f"F1-score : {mean_f1:.4f}\n"
    )

print("\nSaved: eval/results.txt")