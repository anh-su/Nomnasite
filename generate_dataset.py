"""
Tạo dữ liệu huấn luyện tổng hợp (synthetic) cho CRNN Hán Nôm.
Chạy một lần từ thư mục gốc: python generate_dataset.py
"""
import os
import random
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ── Danh sách ký tự Hán Nôm ────────────────────────────────────────────────
CHARS = list(
    "天地人水火山木金土日月星風雨雲雷電春夏秋冬花草樹竹松梅蘭菊荷"
    "龍鳳虎鶴鹿馬牛羊豬狗猫鳥魚蝶蜂"
    "王帝君臣民父母兄弟姐妹子女夫妻友師生"
    "心性命道德仁義禮智信忠孝廉恥"
    "文武詩書易詞賦史志傳記"
    "山河江湖海洋嶺峰谷原野田林森"
    "宮殿廟堂府院城鄉村市街巷門"
    "刀劍弓矢甲兵將帥軍戰勝敗"
    "銀銅鐵玉石珠寶珍貴富貧"
    "南北東西前後左右上下大小長短高低"
    "一二三四五六七八九十百千萬億"
    "年月時刻分秒早晚朝暮晨昏"
    "生死存亡興衰盛古今舊新"
    "愛恨喜悲怒哀樂思念情意志願夢"
    "光明暗黑白紅綠藍紫黃橙青"
    "路橋船車步行走來往"
    "茶酒食飲味香甘苦辛鹹淡"
    "冠帽鞋袍服裳綢絹錦繡"
    "筆墨紙硯畫印刻鑄雕"
    "廣寬深淺遠近多少眾寡"
)

FONT_PATHS = [
    # Windows
    "C:/Windows/Fonts/simsun.ttc",
    "C:/Windows/Fonts/mingliub.ttc",
    "C:/Windows/Fonts/msgothic.ttc",
    # Linux (Streamlit Cloud / Ubuntu)
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/truetype/arphic/uming.ttc",
    "/usr/share/fonts/truetype/arphic/ukai.ttc",
]

FONT_PATH = next((p for p in FONT_PATHS if os.path.exists(p)), None)
if not FONT_PATH:
    raise RuntimeError("Không tìm thấy font CJK. Cần cài font hỗ trợ chữ Hán.")

# ── Hàm tạo ảnh patch ──────────────────────────────────────────────────────
def make_patch(text: str, size: int = 64) -> Image.Image:
    n_chars = len(text)
    w = size * n_chars + 8
    h = size + 8

    # Màu nền parchment nhạt + nhiễu nhẹ
    bg = random.randint(230, 252)
    img = Image.new("RGB", (w, h), (bg, bg - random.randint(0, 8), bg - random.randint(0, 15)))

    # Thêm texture nhẹ
    import numpy as np
    arr = np.array(img, dtype=np.int16)
    noise = np.random.randint(-6, 7, arr.shape, dtype=np.int16)
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    img = Image.fromarray(arr)

    draw = ImageDraw.Draw(img)

    font_size = int(size * random.uniform(0.78, 0.92))
    try:
        font = ImageFont.truetype(FONT_PATH, font_size)
    except Exception:
        font = ImageFont.load_default()

    # Màu mực — đen hoặc nâu đậm
    ink = random.choice([
        (random.randint(0, 30), random.randint(0, 30), random.randint(0, 30)),
        (random.randint(20, 55), random.randint(10, 30), random.randint(0, 15)),
    ])

    x_off = random.randint(2, 5)
    y_off = random.randint(2, 5)
    draw.text((x_off, y_off), text, font=font, fill=ink)

    # Blur rất nhẹ để trông như scan
    if random.random() < 0.4:
        img = img.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.3, 0.7)))

    return img


def gen_label() -> str:
    length = random.choices([1, 2, 3, 4, 5, 6, 7, 8],
                            weights=[5, 15, 20, 20, 15, 10, 8, 7])[0]
    chars = [c for c in CHARS if len(c) == 1]   # chỉ lấy ký tự đơn
    return "".join(random.choices(chars, k=length))


def save_samples(n: int, status: str) -> int:
    img_dir = Path(f"ai/datasets/{status}/images")
    lbl_path = Path(f"ai/datasets/{status}/labels.txt")
    img_dir.mkdir(parents=True, exist_ok=True)

    saved = 0
    with open(lbl_path, "a", encoding="utf-8") as lf:
        for _ in range(n):
            label = gen_label()
            ts = int(time.time() * 1000) + saved   # unique
            fname = f"{label}_{ts}.png"
            fpath = img_dir / fname
            try:
                img = make_patch(label)
                img.save(str(fpath))
                lf.write(f"{fname}|{label}\n")
                saved += 1
            except Exception as e:
                print(f"  skip {label}: {e}")
    return saved


if __name__ == "__main__":
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    print(f"Font: {FONT_PATH}")
    print("approved...", end=" ", flush=True)
    n1 = save_samples(100, "approved")
    print(f"done ({n1})")

    print("pending...", end=" ", flush=True)
    n2 = save_samples(100, "pending")
    print(f"done ({n2})")

    print(f"Total: {n1 + n2}")
