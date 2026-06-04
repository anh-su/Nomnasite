import unicodedata
from pathlib import Path


# Load vocab một lần khi import
_VOCAB_PATH = Path(__file__).parent.parent.parent / "assets" / "vocab.txt"
_VOCAB: set = set()

def _load_vocab():
    global _VOCAB
    if _VOCAB:
        return
    try:
        lines = _VOCAB_PATH.read_text(encoding="utf-8").splitlines()
        _VOCAB = set(c.strip() for c in lines if c.strip())
    except Exception:
        _VOCAB = set()

_load_vocab()


def _is_han_nom_char(ch: str) -> bool:
    """Kiểm tra ký tự có phải Hán Nôm hợp lệ (trong vocab)."""
    if ch in _VOCAB:
        return True
    # fallback: CJK Unicode block
    cp = ord(ch)
    return (
        0x4E00 <= cp <= 0x9FFF or   # CJK Unified
        0x3400 <= cp <= 0x4DBF or   # CJK Extension A
        0x20000 <= cp <= 0x2A6DF or # CJK Extension B
        0xF900 <= cp <= 0xFAFF      # CJK Compatibility
    )


def _vocab_ratio(text: str) -> float:
    """Tỉ lệ ký tự hợp lệ trong chuỗi (bỏ qua khoảng trắng)."""
    chars = [c for c in text if not c.isspace()]
    if not chars:
        return 0.0
    valid = sum(1 for c in chars if _is_han_nom_char(c))
    return valid / len(chars)


def auto_approve(ocr_text: str, corrected_text: str, confidence: float) -> dict:
    """
    Kiểm duyệt correction trước khi đưa vào dataset.

    Nguyên tắc:
    - Reject: rỗng, toàn ASCII, hoặc chứa > 20% ký tự không phải Hán Nôm
    - Pending: mọi trường hợp còn lại (admin phải duyệt thủ công)
    - Approved: KHÔNG auto-approve bất kỳ correction nào của user
                (tránh nhãn sai nhiễm vào dataset)
    """
    text = corrected_text.strip()

    # 1. Rỗng
    if not text:
        return {"status": "rejected", "reason": "empty"}

    # 2. Toàn ký tự ASCII (tiếng Anh, số, v.v.) — không phải Hán Nôm
    if text.isascii():
        return {"status": "rejected", "reason": "ascii_text"}

    # 3. Tỉ lệ ký tự Hán Nôm hợp lệ quá thấp (< 80%)
    ratio = _vocab_ratio(text)
    if ratio < 0.8:
        return {"status": "rejected", "reason": f"low_han_nom_ratio:{ratio:.2f}"}

    # 4. Correction giống hệt OCR gốc → không cung cấp thông tin mới cho dataset
    if text == ocr_text.strip():
        return {"status": "rejected", "reason": "same_as_ocr_no_value"}

    # 5. Mọi correction hợp lệ đều vào pending — admin duyệt thủ công
    return {"status": "pending", "reason": "awaiting_review"}