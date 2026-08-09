import os
import requests
import re
import educatenepal
import jobejee
import merorojgari
import hamrojobs

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


def job_signature(job):
    """A normalized fingerprint (title+company) to catch the same job across portals."""
    title = re.sub(r"[^a-z0-9]", "", job.get("title", "").lower())
    company = re.sub(r"[^a-z0-9]", "", job.get("company", "").lower())
    return f"{title}|{company}"


def load_seen():
    if not os.path.exists(SEEN_FILE):
        return set()
    with open(SEEN_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())


def mark_seen(value):
    with open(SEEN_FILE, "a", encoding="utf-8") as f:
        f.write(value + "\n")


def send_to_telegram(job, source):
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


# each portal's fetcher, wrapped so one failing never stops the others
FETCHERS = [
    ("merojob", merojob.get_jobs),
    ("kumarijob", kumari.get_jobs),
    ("educatenepal", educatenepal.get_jobs),
    ("merorojgari", merorojgari.get_jobs),
    ("hamrojobs", hamrojobs.get_jobs),
    ("jobejee", jobejee.get_jobs),
]


def gather_all_jobs():
    all_jobs = []
    for name, fetch in FETCHERS:
        try:
            portal_jobs = fetch()
            print(f"[{name}] fetched {len(portal_jobs)} jobs")
            for job in portal_jobs:
                job["source"] = name          # remember which portal it came from
            all_jobs.extend(portal_jobs)
        except Exception as e:
            print(f"[{name}] FAILED: {e}")     # one portal failing never stops the others
    return all_jobs


def run():
    seen = load_seen()                      # holds both IDs and signatures from past runs
    jobs = gather_all_jobs()

    new_jobs = []
    sent_signatures = set()                 # signatures sent in THIS run

    for job in jobs:
        if not wanted(job):
            continue
        if job["id"] in seen:               # already sent this exact listing before
            continue

        sig = job_signature(job)
        if sig in seen or sig in sent_signatures:
            continue                        # same job from another portal — skip
        sent_signatures.add(sig)
        new_jobs.append(job)

    print(f"Total {len(jobs)} jobs, {len(new_jobs)} new & matching filter (after dedup).")

    for job in new_jobs:
        send_to_telegram(job, job.get("source", "unknown"))
        mark_seen(job["id"])                # remember the ID
        mark_seen(job_signature(job))       # AND remember the signature
        print(f"Sent: {job['title']}  [{job.get('source')}]")
    print("Done.")


if __name__ == "__main__":
    run()