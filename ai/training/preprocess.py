import cv2
import numpy as np

# Phải khớp với CRNN model input: height=432, width=48, channels=3
IMAGE_HEIGHT = 432
IMAGE_WIDTH = 48


def preprocess_image(image_path):

    image = cv2.imread(image_path)

    if image is None:
        return None

    # BGR → RGB
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    h, w = image.shape[:2]

    # resize giữ tỉ lệ (giống distortion_free_resize của CRNN)
    scale = min(IMAGE_HEIGHT / h, IMAGE_WIDTH / w)
    new_h = int(h * scale)
    new_w = int(w * scale)
    image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_CUBIC)

    # pad về đúng (432, 48, 3) bằng màu trắng
    pad_h = IMAGE_HEIGHT - new_h
    pad_w = IMAGE_WIDTH - new_w
    image = cv2.copyMakeBorder(
        image,
        0, pad_h,
        pad_w // 2, pad_w - pad_w // 2,
        cv2.BORDER_CONSTANT,
        value=(255, 255, 255)
    )

    image = image.astype(np.float32) / 255.0

    return image