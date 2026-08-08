import requests
from bs4 import BeautifulSoup

LIST_URL = "https://merorojgari.com/?post_type=job_listing"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
}


def _job_id_from_url(url):
    slug = url.rstrip("/").split("/")[-1]
    return slug


def get_jobs(page_size=None):
    resp = requests.get(LIST_URL, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    jobs = []
    seen_ids = set()

    # each job is a link to /job/<slug>/
    for link in soup.select('a[href*="/job/"]'):
        title = link.get_text(" ", strip=True)
        url = link.get("href", "").strip()
        if not title or not url:
            continue

        # skip the "Read Post »" duplicate links and anything too short
        if "Read Post" in title or len(title) < 5:
            continue

        job_id = "merorojgari-" + _job_id_from_url(url)
        if job_id in seen_ids:
            continue
        seen_ids.add(job_id)

        jobs.append({
            "id": job_id,
            "title": title,
            "company": "",       # merorojgari lists positions in the title, org varies
            "location": "",      # sometimes in the body, not reliably on the list
            "url": url,
            "posted": "",
            "categories": [],
            "level": "",
        })

    return jobs


if __name__ == "__main__":
    found = get_jobs()
    print(f"Got {len(found)} merorojgari jobs:\n")
    for job in found:
        print(f"- {job['title']}")
        print(f"  {job['url']}")
        print()