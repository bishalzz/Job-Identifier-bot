import requests
from bs4 import BeautifulSoup

SEARCH_URL = "https://www.kumarijob.com/search?sort=newest"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
}


def _job_id_from_url(url):
    last = url.rstrip("/").split("/")[-1]
    number = last.split("-")[0]
    return number if number.isdigit() else last


def get_jobs(page_size=None):
    resp = requests.get(SEARCH_URL, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    jobs = []
    seen_ids = set()

    # each job is its own "card__search" block
    for card in soup.select("div.card__search"):
        title_link = card.select_one("a.job-title-link")
        if not title_link:
            continue
        url = title_link.get("href", "").strip()
        title = title_link.get_text(" ", strip=True)
        if not url or not title:
            continue

        job_id = "kumari-" + _job_id_from_url(url)
        if job_id in seen_ids:
            continue
        seen_ids.add(job_id)

        box = card.select_one("div.location_company_box")
        company = "Unknown company"
        location = ""
        if box:
            comp_link = box.find("a")
            if comp_link:
                company = comp_link.get_text(" ", strip=True)
            meta = box.select_one("span.meta")
            if meta:
                location = meta.get_text(" ", strip=True)

        # tags for THIS card only (job type / level / experience)
        tags = [li.get_text(" ", strip=True)
                for li in card.select("ul.jobtype-level-exp li")]

        jobs.append({
            "id": job_id,
            "title": title,
            "company": company,
            "location": location,
            "url": url,
            "posted": "",
            "categories": tags,
            "level": " ".join(tags),
        })

    return jobs


if __name__ == "__main__":
    found = get_jobs()
    print(f"Got {len(found)} kumarijob jobs:\n")
    for job in found:
        print(f"• {job['title']} — {job['company']} ({job['location']})")
        print(f"  {job['url']}")
        print(f"  tags: {job['categories']}")
        print()