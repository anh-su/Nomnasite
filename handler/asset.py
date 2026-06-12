import io
import os
import shutil
import hashlib
import streamlit as st

from PIL import Image
from urllib.request import urlretrieve
from crnn import CRNN
from dbnet import DBNet


def hash_bytes(bytes_data):
    hash_object = hashlib.sha256(bytes_data)
    hash_str = hash_object.hexdigest()
    return hash_str


@st.cache_resource(show_spinner='Downloading model weights and vocab.txt...')
def download_assets():
    if not os.path.exists('assets.zip'):
        urlretrieve('https://nomnaocr.000webhostapp.com/assets.zip', 'assets.zip')
    if not os.path.exists('assets'):
        shutil.unpack_archive('assets.zip', 'assets')


@st.cache_resource(show_spinner='Loading model weights...')
def load_models():
    det_model = DBNet()
    rec_model = CRNN()
    det_model.model.load_weights('assets/DBNet.h5')

    rec_model.model.load_weights('assets/CRNN.h5')
    return det_model, rec_model


_MAX_IMAGE_BYTES = 200 * 1024 * 1024  # 200 MB


def _compress_to_limit(bytes_data: bytes) -> bytes:
    """Nén ảnh xuống dưới 200 MB bằng cách giảm quality và scale."""
    img = Image.open(io.BytesIO(bytes_data)).convert("RGB")
    quality = 85
    scale = 1.0
    while True:
        if scale < 1.0:
            w, h = img.size
            new_w, new_h = int(w * scale), int(h * scale)
            resized = img.resize((new_w, new_h), Image.LANCZOS)
        else:
            resized = img
        buf = io.BytesIO()
        resized.save(buf, format="JPEG", quality=quality, optimize=True)
        result = buf.getvalue()
        if len(result) <= _MAX_IMAGE_BYTES:
            return result
        # Giảm dần quality rồi scale
        if quality > 40:
            quality -= 10
        else:
            scale *= 0.85


@st.cache_resource(show_spinner='Retrieving image...')
def retrieve_image(uploaded_file, url):
    os.makedirs('./imgs', exist_ok=True)
    if uploaded_file is not None:
        bytes_data = uploaded_file.read()
        if len(bytes_data) > _MAX_IMAGE_BYTES:
            st.info("Ảnh vượt 200 MB, đang nén lại...")
            bytes_data = _compress_to_limit(bytes_data)
        image_path = f'./imgs/{hash_bytes(bytes_data)}.jpg'
        with open(image_path, 'wb') as f:
            f.write(bytes_data)
        return image_path
    elif url:
        bytes_data = url.encode(encoding='utf-8')
        image_path = f'./imgs/{hash_bytes(bytes_data)}.jpg'
        urlretrieve(url, image_path)
        return image_path
    return None