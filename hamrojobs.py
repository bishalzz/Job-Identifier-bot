import requests
from bs4 import BeautifulSoup

LIST_URL = "https://hamrojobs.com.np/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
}


def _job_id_from_url(url):
    # e.g. /jobpost/front-desh-officer/1989 -> 1989 ; /newsjobs/19 -> 19
    return url.rstrip("/").split("/")[-1]


def get_jobs(page_size=None):
    resp = requests.get(LIST_URL, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    jobs = []
    seen_ids = set()

    # both regular jobposts and newspaper jobs
    for link in soup.select('a[href*="/jobpost/"], a[href*="/newsjobs/"]'):
        title = link.get_text(" ", strip=True)
        url = link.get("href", "").strip()
        if not title or not url:
            continue
        if len(title) < 3:          # skip empty/image links
            continue

        # make relative URLs absolute
        if url.startswith("/"):
            url = "https://hamrojobs.com.np" + url

        job_id = "hamrojobs-" + _job_id_from_url(url)
        if job_id in seen_ids:
            continue
        seen_ids.add(job_id)

        jobs.append({
            "id": job_id,
            "title": title,
            "company": "",
            "location": "",
            "url": url,
            "posted": "",
            "categories": [],
            "level": "",
        })

    return jobs


if __name__ == "__main__":
    found = get_jobs()
    print(f"Got {len(found)} hamrojobs listings:\n")
    for job in found:
        print(f"- {job['title']}")
        print(f"  {job['url']}")
        print()