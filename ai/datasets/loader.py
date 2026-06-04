import os


def load_labels(
    images_dir,
    labels_path
):

    dataset = []

    if not os.path.exists(labels_path):

        return dataset

    with open(
        labels_path,
        "r",
        encoding="utf-8"
    ) as f:

        lines = f.readlines()

    for line in lines:

        line = line.strip()

        if "|" not in line:

            continue

        image_name, label = line.split("|")

        image_path = os.path.join(
            images_dir,
            image_name
        )

        # kiểm tra ảnh tồn tại
        if not os.path.exists(image_path):

            continue

        dataset.append({

            "image": image_path,

            "label": label
        })

    return dataset


def load_dataset(
    include_generated=True,
    include_pending=False,
    include_archive=True
):

    dataset = []

    # =========================
    # APPROVED
    # =========================
    dataset += load_labels(
        "ai/datasets/approved/images",
        "ai/datasets/approved/labels.txt"
    )

    # =========================
    # GENERATED
    # =========================
    if include_generated:

        dataset += load_labels(
            "ai/datasets/generated/images",
            "ai/datasets/generated/labels.txt"
        )

    # =========================
    # PENDING
    # =========================
    if include_pending:

        dataset += load_labels(
            "ai/datasets/pending/images",
            "ai/datasets/pending/labels.txt"
        )

    # =========================
    # ARCHIVE (data/archive/Patches)
    # =========================
    if include_archive and os.path.exists("data/archive/Patches"):

        for book in os.listdir("data/archive/Patches"):

            book_dir = os.path.join("data/archive/Patches", book)
            labels_path = os.path.join(book_dir, "labels.txt")

            dataset += load_labels(book_dir, labels_path)

    # =========================
    # REFERENCE CHARS (data/reference_chars)
    # =========================
    dataset += load_labels(
        "data/reference_chars/images",
        "data/reference_chars/labels.txt"
    )

    return dataset