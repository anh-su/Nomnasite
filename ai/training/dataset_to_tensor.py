import numpy as np

from ai.datasets.loader import load_dataset

from ai.training.preprocess import preprocess_image

from ai.training.encoder import (
    build_charset,
    encode_text
)


def dataset_to_tensor():

    dataset = load_dataset()

    # build charset
    charset = build_charset(
        dataset
    )

    X = []

    y = []

    for item in dataset:

        image_path = item["image"]

        label = item["label"]

        # preprocess image
        image = preprocess_image(
            image_path
        )

        if image is None:

            continue

        # encode label
        encoded = encode_text(
            label
        )

        if len(encoded) == 0:

            continue

        X.append(image)

        y.append(encoded)

    X = np.array(
        X,
        dtype=np.float32
    )

    return X, y, charset