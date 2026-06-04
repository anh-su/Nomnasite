import os
import numpy as np
import tensorflow as tf

from tensorflow.keras.optimizers import Adam
from tensorflow.keras import backend as K

from crnn import CRNN
from ai.training.dataset_to_tensor import dataset_to_tensor
from ai.training.ctc_utils import pad_labels


MODEL_PATH      = "assets/CRNN.h5"
NEW_MODEL_PATH  = "assets/CRNN_retrained.h5"
CHECKPOINT_PATH = "assets/CRNN_checkpoint.h5"
META_PATH       = "assets/checkpoint_meta.txt"
EPOCHS          = 10
BATCH_SIZE      = 8


def _save_meta(epoch_done):
    with open(META_PATH, "w") as f:
        f.write(str(epoch_done))


def _load_meta():
    if os.path.exists(META_PATH):
        try:
            return int(open(META_PATH).read().strip())
        except Exception:
            pass
    return 0


def retrain_crnn(on_epoch_end=None) -> list:
    """
    on_epoch_end: callable(epoch, total_epochs, loss) — gọi sau mỗi epoch.
    Trả về list loss theo từng epoch.
    """
    print("=" * 50)
    print("LOADING DATASET")
    print("=" * 50)

    X_train, y_train, charset = dataset_to_tensor()
    y_padded, label_lengths = pad_labels(y_train)

    print(f"Dataset size: {len(X_train)}")
    print(f"Charset size: {len(charset)}")
    print("X_train:", X_train.shape)
    print("y_padded:", y_padded.shape)
    print()

    # =========================
    # BUILD + LOAD WEIGHTS
    # =========================

    print("=" * 50)
    print("LOADING MODEL")
    print("=" * 50)

    crnn = CRNN()

    start_epoch = _load_meta()
    if start_epoch > 0 and os.path.exists(CHECKPOINT_PATH):
        print(f"-> Resume từ checkpoint (đã xong epoch {start_epoch})")
        crnn.model.load_weights(CHECKPOINT_PATH)
    else:
        print("-> Load weights gốc CRNN.h5")
        crnn.model.load_weights(MODEL_PATH)
        start_epoch = 0

    model = crnn.model
    optimizer = Adam(learning_rate=0.0001)

    print()

    # =========================
    # TRAIN VỚI CTC LOSS
    # =========================

    print("=" * 50)
    print(f"START TRAINING (epoch {start_epoch + 1} -> {EPOCHS})")
    print("=" * 50)

    n = len(X_train)
    loss_history = []

    for epoch in range(start_epoch, EPOCHS):

        total_loss = 0.0
        steps = 0

        for i in range(0, n, BATCH_SIZE):

            batch_X = X_train[i:i + BATCH_SIZE]
            batch_y = y_padded[i:i + BATCH_SIZE].astype(np.float32)
            batch_label_len = label_lengths[i:i + BATCH_SIZE].reshape(-1, 1)

            with tf.GradientTape() as tape:

                y_pred = model(batch_X, training=True)

                batch_size = tf.shape(batch_X)[0]
                input_len = tf.shape(y_pred)[1]
                input_lengths_batch = tf.fill([batch_size, 1], tf.cast(input_len, tf.int32))
                label_lengths_tf = tf.cast(batch_label_len, tf.int32)

                loss = K.ctc_batch_cost(
                    batch_y,
                    y_pred,
                    input_lengths_batch,
                    label_lengths_tf
                )
                loss = tf.reduce_mean(loss)

            grads = tape.gradient(loss, model.trainable_variables)
            optimizer.apply_gradients(zip(grads, model.trainable_variables))

            total_loss += float(loss)
            steps += 1

        avg_loss = total_loss / steps
        loss_history.append(avg_loss)
        print(f"Epoch {epoch + 1}/{EPOCHS} — loss: {avg_loss:.4f}")

        if on_epoch_end is not None:
            on_epoch_end(epoch + 1, EPOCHS, avg_loss)

        # lưu checkpoint + meta sau mỗi epoch
        model.save_weights(CHECKPOINT_PATH)
        _save_meta(epoch + 1)

    print()

    # =========================
    # SAVE
    # =========================

    print("=" * 50)
    print("SAVING MODEL")
    print("=" * 50)

    model.save_weights(NEW_MODEL_PATH)
    print(f"Saved weights: {NEW_MODEL_PATH}")

    # xóa meta khi train xong hoàn toàn
    if os.path.exists(META_PATH):
        os.remove(META_PATH)

    return loss_history
    