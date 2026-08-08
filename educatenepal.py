import requests
from bs4 import BeautifulSoup

LIST_URL = "https://www.educatenepal.com/vacancies"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
}


def _job_id_from_url(url):
    slug = url.rstrip("/").split("/")[-1]     # the last part of the detail URL
    return slug


def get_jobs(page_size=None):
    resp = requests.get(LIST_URL, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    jobs = []
    seen_ids = set()

    # every vacancy is a link to /vacancies/detail/...
    for link in soup.select('a[href*="/vacancies/detail/"]'):
        title = link.get_text(" ", strip=True)
        url = link.get("href", "").strip()
        if not title or not url:
            continue

        # skip image-only links (no visible text) and trending duplicates
        if len(title) < 5:
            continue

        job_id = "educatenepal-" + _job_id_from_url(url)
        if job_id in seen_ids:
            continue
        seen_ids.add(job_id)

        jobs.append({
            "id": job_id,
            "title": title,
            "company": "",          # educatenepal puts the org inside the title text
            "location": "",         # not shown on the list page
            "url": url,
            "posted": "",
            "categories": [],       # no per-job tags on the list page
            "level": "",
        })

    return jobs


if __name__ == "__main__":
    found = get_jobs()
    print(f"Got {len(found)} educatenepal vacancies:\n")
    for job in found:
        print(f"- {job['title']}")
        print(f"  {job['url']}")
        print()