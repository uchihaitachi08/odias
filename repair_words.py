# clean_words_strict.py
import json, unicodedata, re

IN  = "dictionary.json"
OUT = "dictionary.cleaned.json"

ODIA = re.compile(r"[\u0B00-\u0B7F]")

def strip_internals(word: str) -> str:
    if not word: return word
    chars = list(word)
    keep = []
    n = len(chars)
    for i, ch in enumerate(chars):
        cat = unicodedata.category(ch)
        if 0 < i < n-1 and ODIA.match(chars[i-1]) and ODIA.match(chars[i+1]) and cat in {"Cf","Zs","Zl","Zp"}:
            # drop invisible/space *between* Odia letters
            continue
        keep.append(ch)
    fixed = "".join(keep)
    return unicodedata.normalize("NFC", fixed)

with open(IN, "r", encoding="utf-8") as f:
    data = json.load(f)

changed = 0
for e in data:
    w = e.get("word", "")
    neww = strip_internals(w)
    if neww != w:
        e["word"] = neww
        changed += 1

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Cleaned {changed} words → {OUT}")

