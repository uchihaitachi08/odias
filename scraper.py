import json, time, random, threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://dsal.uchicago.edu/cgi-bin/app/praharaj_query.py?page={}"
START_PAGE = 1
END_PAGE = 9248
OUTPUT_FILE = "odia_dictionary_full.json"

MAX_THREADS = 8          # start conservative; raise to 10–12 if stable
MAX_RETRIES = 3          # our own page-level retries (in addition to HTTPAdapter retries)
RETRY_DELAY = 2          # seconds between our retries
TIMEOUT = (10, 30)       # (connect, read) seconds

# --- Thread-safe session factory with HTTP retry/backoff ---
_tls = threading.local()

def get_session():
    if not hasattr(_tls, "session"):
        s = requests.Session()
        retry = Retry(
            total=5,                # HTTP-layer retries (separate from our page loop)
            connect=5,
            read=5,
            backoff_factor=1.5,     # exponential backoff: 0, 1.5, 3.0, 4.5, ...
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry, pool_connections=MAX_THREADS, pool_maxsize=MAX_THREADS)
        s.mount("https://", adapter)
        s.mount("http://", adapter)
        s.headers.update({"User-Agent": "OTV-Odia-Dict-Scraper/1.0 (+contact@yourdomain)"})
        _tls.session = s
    return _tls.session

# --- Parsing ---
from bs4 import BeautifulSoup

def parse_entries(html, page_num):
    soup = BeautifulSoup(html, "html.parser")
    out = []
    for entry in soup.find_all("entry"):
        word_tag = entry.find("b")
        tr_tag = entry.find("tr")
        sense_tag = entry.find("sense")

        word = word_tag.get_text(strip=True) if word_tag else ""
        translit = tr_tag.get_text(strip=True) if tr_tag else ""
        desc = sense_tag.get_text(" ", strip=True) if sense_tag else ""

        if word or translit or desc:
            out.append({
                "page": page_num,
                "word": word,
                "transliteration": translit,
                "description": desc
            })
    return out

# --- Scrape one page with our own retry loop ---
def scrape_page(page_num):
    sess = get_session()
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # small jitter to avoid thundering herd
            time.sleep(random.uniform(0.05, 0.2))
            resp = sess.get(BASE_URL.format(page_num), timeout=TIMEOUT)
            if resp.status_code != 200:
                print(f"⚠️ page {page_num}: HTTP {resp.status_code}, attempt {attempt}")
                time.sleep(RETRY_DELAY * attempt)
                continue
            entries = parse_entries(resp.text, page_num)
            print(f"✅ page {page_num}: {len(entries)} entries")
            return entries
        except requests.exceptions.RequestException as e:
            print(f"❌ page {page_num} attempt {attempt}: {e}")
            time.sleep(RETRY_DELAY * attempt)
    # give up after MAX_RETRIES
    return None

def main():
    all_entries = []
    failed = []

    # First pass (parallel)
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as ex:
        futs = {ex.submit(scrape_page, p): p for p in range(START_PAGE, END_PAGE + 1)}
        for fut in as_completed(futs):
            p = futs[fut]
            res = fut.result()
            if res is None:
                failed.append(p)
            else:
                all_entries.extend(res)

    # Second pass (sequential, slower but sturdier) for failed pages
    if failed:
        print(f"🔁 Retrying {len(failed)} failed pages sequentially with longer timeouts...")
        failed2 = []
        seq_sess = requests.Session()
        # beefier retry for the sequential pass
        retry = Retry(total=6, connect=6, read=6, backoff_factor=2.0,
                      status_forcelist=[429, 500, 502, 503, 504],
                      allowed_methods=["GET"], raise_on_status=False)
        adapter = HTTPAdapter(max_retries=retry)
        seq_sess.mount("https://", adapter)
        seq_sess.headers.update({"User-Agent": "OTV-Odia-Dict-Scraper/1.0 (+contact@yourdomain)"})

        long_timeout = (15, 60)
        for p in sorted(failed):
            ok = False
            for attempt in range(1, 4):
                try:
                    time.sleep(0.3 + 0.2 * attempt)
                    r = seq_sess.get(BASE_URL.format(p), timeout=long_timeout)
                    if r.status_code == 200:
                        entries = parse_entries(r.text, p)
                        all_entries.extend(entries)
                        print(f"✅ (seq) page {p}: {len(entries)} entries")
                        ok = True
                        break
                    else:
                        print(f"⚠️ (seq) page {p}: HTTP {r.status_code}, attempt {attempt}")
                except requests.exceptions.RequestException as e:
                    print(f"❌ (seq) page {p} attempt {attempt}: {e}")
            if not ok:
                failed2.append(p)

        failed = failed2

    # Finalize
    all_entries.sort(key=lambda x: x["page"])
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_entries, f, ensure_ascii=False, indent=2)

    print(f"🎉 Saved {len(all_entries)} entries to {OUTPUT_FILE}")
    if failed:
        print(f"⛔ Still failed pages ({len(failed)}): {failed[:20]}{' ...' if len(failed)>20 else ''}")

if __name__ == "__main__":
    main()

