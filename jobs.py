import requests

API_URL = "https://api.merojob.com/api/v1/jobs/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
    "Origin": "https://merojob.com",
    "Referer": "https://merojob.com/",
}


def get_jobs(page_size=30):
    """Fetch the newest jobs from merojob and return a clean list."""
    params = {"page": 1, "page_size": page_size}
    resp = requests.get(API_URL, params=params, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    data = resp.json()

    jobs = []
    for item in data.get("results", []):
        client = item.get("client") or {}
        company = client.get("client_name", "Unknown company")

        locations = item.get("job_locations") or []
        location = locations[0].get("address", "") if locations else ""

        url = "https://merojob.com" + (item.get("absolute_url") or "")

        jobs.append({
            "id": str(item.get("id")),
            "title": item.get("title", "No title"),
            "company": company,
            "location": location,
            "url": url,
            "posted": item.get("posted_date", ""),
            "categories": item.get("categories") or [],   # NEW
            "level": item.get("job_level", ""),           # NEW
        })

    return jobs


if __name__ == "__main__":
    for job in get_jobs():
        print(job["title"], "|", job["categories"], "|", job["level"])