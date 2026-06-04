"""
Pipeline: correction của user → image patch → dataset approved/pending.

Mỗi lần user lưu correction trong trang Dịch nâng cao:
  1. crop patch đã có sẵn
  2. auto_approve() quyết định routing
  3. save_patch() ghi vào ai/datasets/<status>/
"""

from ai.datasets.builder import save_patch
from ai.moderation.moderator import auto_approve


def save_patch_from_correction(patch_img, ocr_text: str, corrected_text: str, confidence: float) -> str | None:
    """
    Lưu patch ảnh + nhãn vào dataset.

    Args:
        patch_img:      numpy array (H, W, 3) — ảnh crop của box
        ocr_text:       văn bản CRNN nhận dạng gốc
        corrected_text: văn bản người dùng đã sửa
        confidence:     float 0–1 (accuracy / 100)

    Returns:
        "approved" | "pending" | "rejected" | None
    """
    if not corrected_text or not corrected_text.strip():
        return None

    result = auto_approve(ocr_text, corrected_text, confidence)
    status = result.get("status", "pending")

    if status == "rejected":
        return "rejected"

    try:
        save_patch(patch_img, corrected_text.strip(), status=status)
        return status
    except Exception:
        return None


def get_dataset_stats() -> dict:
    """Thống kê số lượng mẫu trong từng folder dataset."""
    import os

    def _count(label_path: str) -> int:
        if not os.path.exists(label_path):
            return 0
        try:
            return sum(1 for line in open(label_path, encoding="utf-8") if "|" in line)
        except Exception:
            return 0

    return {
        "approved":  _count("ai/datasets/approved/labels.txt"),
        "pending":   _count("ai/datasets/pending/labels.txt"),
        "generated": _count("ai/datasets/generated/labels.txt"),
        "rejected":  _count("ai/datasets/rejected/labels.txt"),
    }


def approve_all_pending() -> int:
    """Chuyển toàn bộ pending → approved. Trả về số mẫu được duyệt."""
    import os
    import shutil

    src_img = "ai/datasets/pending/images"
    src_lbl = "ai/datasets/pending/labels.txt"
    dst_img = "ai/datasets/approved/images"
    dst_lbl = "ai/datasets/approved/labels.txt"

    if not os.path.exists(src_lbl):
        return 0

    os.makedirs(dst_img, exist_ok=True)

    lines = []
    try:
        with open(src_lbl, encoding="utf-8") as f:
            lines = [l for l in f if "|" in l]
    except Exception:
        return 0

    count = 0
    for line in lines:
        fname = line.split("|")[0].strip()
        src_path = os.path.join(src_img, fname)
        dst_path = os.path.join(dst_img, fname)
        if os.path.exists(src_path):
            shutil.copy(src_path, dst_path)
            count += 1

    if count:
        with open(dst_lbl, "a", encoding="utf-8") as f:
            f.writelines(lines)
        # xóa pending
        open(src_lbl, "w").close()
        for fname in os.listdir(src_img):
            try:
                os.remove(os.path.join(src_img, fname))
            except Exception:
                pass

    return count
