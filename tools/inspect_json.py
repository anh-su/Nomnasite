import json, os, re, sys
sys.stdout.reconfigure(encoding='utf-8')

RAW_BASE = "data/archive/Raw"

for book in sorted(os.listdir(RAW_BASE)):
    raw_dir = os.path.join(RAW_BASE, book)
    if not os.path.isdir(raw_dir):
        continue

    automa_path = os.path.join(raw_dir, "automa.json")
    if not os.path.exists(automa_path):
        continue

    data = json.load(open(automa_path, encoding="utf-8"))
    print(f"=== {book}/automa.json ===")
    print(f"  Type: {type(data).__name__}, len: {len(data) if isinstance(data, list) else 'N/A'}")

    if isinstance(data, list) and data:
        e0 = data[0]
        print(f"  Keys: {list(e0.keys())}")
        url = e0.get("url", "")
        print(f"  url[0]: {url}")
        text = str(e0.get("text", ""))[:300]
        print(f"  text[0] (300c): {text}")
    elif isinstance(data, dict):
        print(f"  Keys (top-level): {list(data.keys())[:10]}")
    print()
