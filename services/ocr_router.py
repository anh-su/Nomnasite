import cv2
import numpy as np


def preprocess_patch(patch):
    # Xoay ảnh thành dọc nếu đang nằm ngang (CRNN cần ảnh cao x rộng = 432x48)
    h, w = patch.shape[:2]
    if w > h:
        patch = cv2.rotate(patch, cv2.ROTATE_90_CLOCKWISE)

    # Chuyển sang grayscale để tăng cường độ tương phản
    gray = cv2.cvtColor(patch, cv2.COLOR_RGB2GRAY)

    # CLAHE: tăng tương phản cục bộ, giúp chữ nét hơn
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))
    enhanced = clahe.apply(gray)

    # Lọc nhiễu nhẹ
    denoised = cv2.fastNlMeansDenoising(enhanced, h=7, templateWindowSize=7, searchWindowSize=21)

    # Trả về ảnh 3 kênh như CRNN mong đợi
    return cv2.cvtColor(denoised, cv2.COLOR_GRAY2RGB)


def recognize_auto(patch, crnn_model):
    patch = preprocess_patch(patch)
    result = crnn_model.predict_top_k(patch, top_k=1)
    if result:
        return result[0][0], "crnn"
    return "", "crnn"
