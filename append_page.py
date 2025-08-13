import json
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://dsal.uchicago.edu/cgi-bin/app/praharaj_query.py?page={}"
PAGE_NUM = 9248
JSON_FILE = "odia_dictionary_full.json"

def scrape_page(page_num):
    url = BASE_URL.format(page_num)
    resp = requests.get(url, timeout=(10, 30))
    resp.encoding = 'utf-8'

    if resp.status_code != 200:
        print(f"❌ Failed to fetch page {page_num} - HTTP {resp.status_code}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    entries = []

    for entry in soup.find_all("entry"):
        word_tag = entry.find("b")
        tr_tag = entry.find("tr")
        sense_tag = entry.find("sense")

        word = word_tag.get_text(strip=True) if word_tag else ""
        translit = tr_tag.get_text(strip=True) if tr_tag else ""
        desc = sense_tag.get_text(" ", strip=True) if sense_tag else ""

        if word or translit or desc:
            entries.append({
                "page": page_num,
                "word": word,
                "transliteration": translit,
                "description": desc
            })

    print(f"✅ Scraped page {page_num}: {len(entries)} entries")
    return entries

def main():
    # Load existing JSON
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Check if page 9248 already exists
    if any(entry["page"] == PAGE_NUM for entry in data):
        print(f"⚠️ Page {PAGE_NUM} already exists in {JSON_FILE}")
        return

    # Scrape new page
    new_entries = scrape_page(PAGE_NUM)

    if not new_entries:
        print("❌ No entries found to append.")
        return

    # Append and sort
    data.extend(new_entries)
    data.sort(key=lambda x: x["page"])

    # Save back to file
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"🎉 Page {PAGE_NUM} appended successfully to {JSON_FILE}")

if __name__ == "__main__":
    main()

