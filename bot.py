import os
import requests
import re
import educatenepal

import jobs as merojob          # your merojob fetcher (jobs.py)
import kumari                   # your kumarijob fetcher (kumari.py)

TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

SEEN_FILE = "seen.txt"

IT_KEYWORDS = [
    # development
    "developer", "software development", "web development", "software",
    "programmer", "programming",
    "web develop", "frontend", "front-end", "front end",
    "backend", "back-end", "back end", "full stack", "fullstack", "full-stack",
    "python", "java", "javascript", "php", ".net", "dotnet",
    "react", "angular", "vue", "node", "django", "laravel", "flutter",
    "android", "ios develop", "mobile app", "app develop",
    "wordpress", "ui/ux", "ux design", "ui design", "web design",
    "software engineer", "qa engineer", "quality assurance",
    "software tester", "test engineer", "automation",
    # data / cloud / security
    "data engineer", "data analyst", "data scientist", "data science",
    "machine learning", "artificial intelligence", " ai ", "ai engineer",
    "devops", "cloud", "aws", "azure",
    "cybersecurity", "cyber security", "information security",
    "database", "sql",
    # networking / systems
    "network", "networking", "noc", "ccna", "ccnp",
    "system admin", "systems admin", "sysadmin", "sys admin",
    "infrastructure", "server admin",
    "linux", "telecom", "telecommunication",
    # generic / broad IT
    "it officer", "it support", "it manager", "it head",
    "it administrator", "it admin", "it engineer", "it executive",
    "it trainee", "it intern", "it associate", "it assistant",
    "information technology", "system engineer", "system analyst",
    "technical support", "tech support", "technical officer",
    "it technician", "computer", "hardware", "helpdesk", "help desk",
    "erp", "odoo", "seo", "digital", "graphic",
]

IT_CATEGORY_HINTS = [
    "information technology", "it &", "& it", "it ", " it",
    "telecommunication", "computer", "software", "network", "tech",
]


def wanted(job):
    title = job["title"].lower()
    cats = " ".join(job.get("categories", [])).lower()
    if any(hint in cats for hint in IT_CATEGORY_HINTS):
        return True
    if any(kw in title for kw in IT_KEYWORDS):
        return True
    return False


def load_seen():
    if not os.path.exists(SEEN_FILE):
        return set()
    with open(SEEN_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())


def mark_seen(job_id):
    with open(SEEN_FILE, "a", encoding="utf-8") as f:
        f.write(job_id + "\n")


def send_to_telegram(job):
    source = "merojob" if job["id"].isdigit() else "kumarijob"
    text = (
        f"🆕 {job['title']}\n"
        f"🏢 {job['company']}\n"
        f"📍 {job['location']}\n"
        f"🌐 {source}\n"
        f"🔗 {job['url']}"
    )
    resp = requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": text},
        timeout=20,
    )
    resp.raise_for_status()


# each portal's fetcher, wrapped so one failing never stops the other
FETCHERS = [
    ("merojob", merojob.get_jobs),
    ("kumarijob", kumari.get_jobs),
    ("educatenepal", educatenepal.get_jobs),
]


def gather_all_jobs():
    all_jobs = []
    for name, fetch in FETCHERS:
        try:
            portal_jobs = fetch()
            print(f"[{name}] fetched {len(portal_jobs)} jobs")
            all_jobs.extend(portal_jobs)
        except Exception as e:
            print(f"[{name}] FAILED: {e}")     # keep going with the other portal
    return all_jobs


def run():
    seen = load_seen()
    jobs = gather_all_jobs()
    new_jobs = [j for j in jobs if wanted(j) and j["id"] not in seen]
    print(f"Total {len(jobs)} jobs, {len(new_jobs)} new & matching filter.")
    for job in new_jobs:
        send_to_telegram(job)
        mark_seen(job["id"])
        print(f"Sent: {job['title']}")
    print("Done.")


if __name__ == "__main__":
    run()