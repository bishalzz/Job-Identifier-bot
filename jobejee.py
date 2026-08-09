import requests
from bs4 import BeautifulSoup

LIST_URL = "https://jobejee.com/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
}


def _job_id_from_url(url):
    # e.g. /job/Nodejs-Developer/48328 -> 48328
    return url.rstrip("/").split("/")[-1]


def get_jobs(page_size=None):
    resp = requests.get(LIST_URL, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    jobs = []
    seen_ids = set()

    # each job is a link like /job/<Title>/<id>
    for link in soup.select('a[href*="/job/"]'):
        url = link.get("href", "").strip()
        title = link.get_text(" ", strip=True)
        if not url or not title:
            continue

        job_id_raw = _job_id_from_url(url)
        if not job_id_raw.isdigit():      # only real job links end in a number
            continue

        # make absolute if needed
        if url.startswith("/"):
            url = "https://jobejee.com" + url

        job_id = "jobejee-" + job_id_raw
        if job_id in seen_ids:
            continue
        seen_ids.add(job_id)

        # the company is usually the next employer link after the job
        company = ""
        parent = link.find_parent()
        if parent:
            emp = parent.find("a", href=lambda h: h and "/employer/" in h)
            if emp:
                company = emp.get_text(" ", strip=True)

        jobs.append({
            "id": job_id,
            "title": title,
            "company": company,
            "location": "",
            "url": url,
            "posted": "",
            "categories": [],
            "level": "",
        })

    return jobs


if __name__ == "__main__":
    found = get_jobs()
    print(f"Got {len(found)} jobejee jobs:\n")
    for job in found:
        print(f"- {job['title']}  ({job['company']})")
        print(f"  {job['url']}")
        print()