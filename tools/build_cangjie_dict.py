"""
Download cangjie5.base.dict.yaml from RIME GitHub and build an inverted index
{code: "chars"} saved to data/cangjie5.json.
"""
import sys, json, urllib.request, os

sys.stdout.reconfigure(encoding="utf-8")

URL = "https://raw.githubusercontent.com/rime/rime-cangjie/master/cangjie5.base.dict.yaml"
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "cangjie5.json")

print("Downloading cangjie5.base.dict.yaml ...")
try:
    with urllib.request.urlopen(URL, timeout=30) as r:
        raw = r.read().decode("utf-8")
except Exception as e:
    print(f"Download failed: {e}")
    sys.exit(1)

print(f"Downloaded {len(raw):,} bytes. Parsing ...")

# Skip YAML header (lines starting with # or containing : or starting with -)
# Data lines look like: "日\ta" or "晶\taaa"
inverted = {}  # code -> list of chars
in_data = False
count = 0
for line in raw.splitlines():
    line = line.strip()
    if not line:
        continue
    if line == "...":  # YAML document end, data starts after this? No.
        in_data = True
        continue
    if line.startswith("#") or ":" in line or line.startswith("-"):
        continue
    # Try to parse as data line: char\tcode or char\tcode\tstem
    parts = line.split("\t")
    if len(parts) >= 2:
        char, code = parts[0], parts[1]
        if len(char) == 1 and code.isalpha() and code.islower():
            if code not in inverted:
                inverted[code] = ""
            inverted[code] += char
            count += 1

print(f"Parsed {count:,} entries, {len(inverted):,} unique codes.")

# Sort by code length for nicer output
result = dict(sorted(inverted.items(), key=lambda x: (len(x[0]), x[0])))

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, separators=(",", ":"))

size = os.path.getsize(OUT)
print(f"Saved to {OUT} ({size:,} bytes)")
