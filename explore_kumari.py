import requests
from bs4 import BeautifulSoup

URL = "https://www.kumarijob.com/search?sort=newest"
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "text/html"}

resp = requests.get(URL, headers=HEADERS, timeout=20)
print("Status:", resp.status_code)
soup = BeautifulSoup(resp.text, "html.parser")

# A) Check for hidden structured data (clean path if present)
ld = soup.find_all("script", type="application/ld+json")
print("JSON-LD blocks found:", len(ld))
for i, s in enumerate(ld[:3]):
    print(f"--- block {i} (first 400 chars) ---")
    print((s.string or "(empty)")[:400])

# B) Find real job links (last URL part contains a number)
def looks_like_job(href):
    last = href.rstrip("/").split("/")[-1]
    has_digit = any(c.isdigit() for c in last)
    return "kumarijob.com" in href and has_digit and "jobs-in-nepal" not in href and "jobs-by" not in href

print("=== Candidate job links (first 12) ===")
seen = []
first = None
for a in soup.find_all("a", href=True):
    if looks_like_job(a["href"]):
        if first is None:
            first = a
        if a["href"] not in seen:
            seen.append(a["href"])
            print(repr(a.get_text(" ", strip=True)[:55]), "->", a["href"])
        if len(seen) >= 12:
            break

# C) Show structure of the first job card
if first is not None:
    card = first
    for _ in range(5):
        if card.parent is not None:
            card = card.parent
    print("=== First job card structure (trimmed) ===")
    print(card.prettify()[:2500])
else:
    print("No job-detail links found — we'll adjust.")