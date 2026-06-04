VOCAB_PATH = "assets/vocab.txt"

# Load vocab từ file — phải khớp với StringLookup trong CRNN model
# Index 0 = [PAD], Index 1 = [UNK], Index 2+ = ký tự thực
_vocab = open(VOCAB_PATH, encoding='utf-8').read().splitlines()
CHARSET = _vocab  # giữ nguyên thứ tự vocab.txt


def build_charset(dataset):
    # Không rebuild từ dataset — luôn dùng vocab.txt để khớp với model
    return CHARSET


def encode_text(text):
    encoded = []
    for ch in text:
        if ch in CHARSET:
            encoded.append(CHARSET.index(ch))
        # bỏ qua ký tự không có trong vocab
    return encoded


def decode_text(indices):
    text = ""
    for idx in indices:
        if 0 <= idx < len(CHARSET):
            text += CHARSET[idx]
    return text