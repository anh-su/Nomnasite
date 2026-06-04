import shutil
import os


def merge_datasets():

    sources = [

        "ai/datasets/generated/images",

        "ai/datasets/approved/images"
    ]

    target = "ai/datasets/train/images"

    os.makedirs(
        target,
        exist_ok=True
    )

    for source in sources:

        if not os.path.exists(source):

            continue

        for file in os.listdir(source):

            src_path = os.path.join(
                source,
                file
            )

            dst_path = os.path.join(
                target,
                file
            )

            shutil.copy(
                src_path,
                dst_path
            )