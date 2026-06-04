import os
import time

from PIL import Image


def get_dataset_paths(status):

    base_dir = f"ai/datasets/{status}"

    image_dir = os.path.join(
        base_dir,
        "images"
    )

    labels_path = os.path.join(
        base_dir,
        "labels.txt"
    )

    return image_dir, labels_path


def append_label(
    image_name,
    label,
    labels_path
):

    os.makedirs(
        os.path.dirname(labels_path),
        exist_ok=True
    )

    with open(
        labels_path,
        "a",
        encoding="utf-8"
    ) as f:

        f.write(
            f"{image_name}|{label}\n"
        )


def save_patch(
    patch,
    label,
    status="pending"
):

    # lấy path theo status
    dataset_dir, labels_path = get_dataset_paths(
        status
    )

    # tạo folder
    os.makedirs(
        dataset_dir,
        exist_ok=True
    )

    # unique filename
    filename = f"{label}_{int(time.time()*1000)}.png"

    path = os.path.join(
        dataset_dir,
        filename
    )

    # numpy -> PIL
    if not isinstance(patch, Image.Image):

        patch = Image.fromarray(patch)

    # save image
    patch.save(path)

    # append labels
    append_label(
        filename,
        label,
        labels_path
    )

    return path