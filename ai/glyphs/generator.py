import os

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont


FONT_PATH = "ai/glyphs/fonts/HanaMinA.otf"

DATASET_DIR = "ai/datasets/generated/images"

LABELS_PATH = "ai/datasets/generated/labels.txt"


def append_label(
    image_name,
    char
):

    os.makedirs(
        os.path.dirname(LABELS_PATH),
        exist_ok=True
    )

    # tránh duplicate
    if os.path.exists(LABELS_PATH):

        with open(
            LABELS_PATH,
            "r",
            encoding="utf-8"
        ) as f:

            lines = f.readlines()

            for line in lines:

                if line.strip() == f"{image_name}|{char}":

                    return

    with open(
        LABELS_PATH,
        "a",
        encoding="utf-8"
    ) as f:

        f.write(
            f"{image_name}|{char}\n"
        )


def generate_glyph(
    char,
    font_size=128,
    image_size=160
):

    # tạo folder dataset
    os.makedirs(
        DATASET_DIR,
        exist_ok=True
    )

    # load font
    font = ImageFont.truetype(
        FONT_PATH,
        font_size
    )

    # tạo ảnh trắng
    img = Image.new(
        "RGB",
        (image_size, image_size),
        "white"
    )

    draw = ImageDraw.Draw(img)

    # căn giữa
    bbox = draw.textbbox(
        (0, 0),
        char,
        font=font
    )

    text_width = bbox[2] - bbox[0]

    text_height = bbox[3] - bbox[1]

    x = (image_size - text_width) // 2

    y = (image_size - text_height) // 2

    # vẽ chữ
    draw.text(
        (x, y),
        char,
        font=font,
        fill="black"
    )

    # tránh overwrite
    image_name = f"{char}_{font_size}.png"

    output_path = os.path.join(
        DATASET_DIR,
        image_name
    )

    # save ảnh
    img.save(output_path)

    # save label
    append_label(
        image_name,
        char
    )

    return output_path