import json

# Paths
INPUT_FILE = "dictionary.json"
OUTPUT_FILE = "verbs.json"

# Load dictionary
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

# Filter: "1. To" appears anywhere in description
verbs = [
    entry for entry in data
    if isinstance(entry.get("description"), str)
    and "1. To " in entry["description"]
]

# Save filtered verbs
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(verbs, f, ensure_ascii=False, indent=2)

print(f"Found {len(verbs)} verbs. Saved to {OUTPUT_FILE}.")

