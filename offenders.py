# inspect_hidden_chars.py
import json, unicodedata, re

PATH = "dictionary.json"

with open(PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

ODIA = re.compile(r"[\u0B00-\u0B7F]")

def dump(s):
    for i, ch in enumerate(s):
        print(f"{i:>2}: {ch}  U+{ord(ch):04X}  {unicodedata.name(ch, 'UNKNOWN')}  cat={unicodedata.category(ch)}")

for e in data:
    w = e.get("word","")
    # detect any separator/format char between Odia letters
    for i in range(1, len(w)-1):
        if ODIA.match(w[i-1]) and ODIA.match(w[i+1]):
            cat = unicodedata.category(w[i])
            if cat in ("Cf","Zs","Zl","Zp") or w[i] in " \u00A0\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200A\u202F\u205F\u200B\u200C\u200D\u2060\uFEFF":
                print("\nPAGE", e.get("page"), "WORD =", repr(w))
                dump(w)
                break

