import numpy as np


MAX_LABEL_LENGTH = 32


def pad_labels(labels):

    padded = []

    lengths = []

    for label in labels:

        lengths.append(
            len(label)
        )

        # padding
        padded_label = label + (
            [0] * (
                MAX_LABEL_LENGTH
                - len(label)
            )
        )

        padded.append(
            padded_label[:MAX_LABEL_LENGTH]
        )

    return (

        np.array(
            padded,
            dtype=np.int32
        ),

        np.array(
            lengths,
            dtype=np.int32
        )
    )


def create_input_lengths(
    batch_size,
    time_steps=32
):

    return np.full(
        shape=(batch_size, 1),
        fill_value=time_steps,
        dtype=np.int32
    )