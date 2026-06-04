from tensorflow.keras.models import load_model

from ai.datasets.loader import load_dataset


MODEL_PATH = "models/crnn/CRNN.h5"


def retrain_crnn():

    print("=" * 50)

    print("LOADING MODEL")

    print("=" * 50)

    model = load_model(
        MODEL_PATH,
        compile=False
    )

    dataset = load_dataset()

    print(f"Dataset size: {len(dataset)}")

    print()

    print("READY FOR RETRAINING")

    return model