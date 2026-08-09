# Job Notifier Bot — Complete Project Guide

A Telegram bot that watches Kathmandu job portals (merojob + kumarijob) and
sends you a message whenever a **new IT / networking / development job** is
posted. It runs itself every 30 minutes on GitHub Actions — free, and even when
your computer is off.

This document is your full reference: how it works, every file's contents, and
step-by-step instructions for extending it (adding portals, tuning filters,
changing the schedule).

---

## 1. What you built (the big picture)

```
   every 30 min (GitHub Actions cron)
              |
              v
        bot.py  ──asks──>  jobs.py     (merojob — hidden JSON API)
              |            kumari.py    (kumarijob — HTML scraping)
              |
              |  combines all jobs, keeps only IT/dev/networking ones
              |  that aren't already in seen.txt
              v
        Telegram  ──>  your phone
              |
              v
     saves seen.txt back to the GitHub repo (so it remembers next run)
```

**The pattern behind it (reusable for almost any bot):**
fetch → filter → notify → remember → schedule.

---

## 2. How each portal's data is fetched

Two portals, two different techniques — worth understanding because any *new*
portal you add will be one of these cases.

- **merojob → hidden JSON API.** Its jobs are loaded by JavaScript from a clean
  data endpoint: `https://api.merojob.com/api/v1/jobs/`. We call it directly and
  get tidy JSON. This is the *best* case — stable and clean.
  (Found via browser DevTools → Network tab, watching what fired on search.)

- **kumarijob → HTML scraping.** Its jobs are baked into the page HTML
  (server-rendered). We fetch the page and pull job cards out with BeautifulSoup,
  targeting `div.card__search`. More fragile — if they redesign, selectors need
  updating — but simple.

**The decision procedure for ANY new portal:**
1. Does it have an **RSS feed**? (try `/feed`, `/rss`) → easiest, use `feedparser`.
2. Does it have a **hidden JSON API**? (DevTools → Network → Fetch/XHR, reload or
   search, look for a request returning job data) → use `requests` + `.json()`.
3. Neither, but **jobs are in the page HTML**? → scrape with `requests` +
   `BeautifulSoup`.
4. Page HTML is empty (JS-only) and no findable API? → needs a real-browser tool
   like Playwright (heavier — avoid unless necessary).

---

## 3. The files

Your project folder contains these. The **core files** (needed to run) are
`bot.py`, `jobs.py`, `kumari.py`, `requirements.txt`, `.gitignore`, and
`.github/workflows/bot.yml`. The `explore_*.py`, `check_filter.py`, and
`hello.py` files were just for building/testing and can be ignored or deleted.

### 3.1 `jobs.py` — merojob fetcher (JSON API)

```python
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
            "categories": item.get("categories") or [],
            "level": item.get("job_level", ""),
        })

    return jobs


if __name__ == "__main__":
    for job in get_jobs():
        print(job["title"], "|", job["categories"], "|", job["level"])
```

### 3.2 `kumari.py` — kumarijob fetcher (HTML scraping)

```python
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
        print(f"- {job['title']} - {job['company']} ({job['location']})")
        print(f"  {job['url']}")
        print(f"  tags: {job['categories']}")
        print()
```

### 3.3 `bot.py` — the brain (combine, filter, notify, remember)

```python
import os
import re
import requests

import jobs as merojob          # merojob fetcher (jobs.py)
import kumari                   # kumarijob fetcher (kumari.py)

TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

SEEN_FILE = "seen.txt"

# ---- FILTER: keep only IT / networking / development jobs ----
IT_KEYWORDS = [
    "developer", "development", "software", "programmer", "programming",
    "web develop", "frontend", "front-end", "front end",
    "backend", "back-end", "back end", "full stack", "fullstack", "full-stack",
    "python", "java", "javascript", "php", ".net", "dotnet",
    "react", "angular", "vue", "node", "django", "laravel", "flutter",
    "android", "ios develop", "mobile app", "app develop",
    "wordpress", "ui/ux", "ux design", "ui design", "web design",
    "software engineer", "qa engineer", "quality assurance",
    "software tester", "test engineer", "automation",
    "data engineer", "data analyst", "data scientist", "data science",
    "machine learning", "artificial intelligence", "ai engineer",
    "devops", "cloud", "aws", "azure",
    "cybersecurity", "cyber security", "information security",
    "database", "sql",
    "network", "networking", "noc", "ccna", "ccnp",
    "system admin", "systems admin", "sysadmin", "sys admin",
    "infrastructure", "server admin",
    "linux", "telecom", "telecommunication",
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
    """True if this job is IT / networking / development (whole-word match)."""
    title = job["title"].lower()
    cats = " ".join(job.get("categories", [])).lower()

    if any(hint in cats for hint in IT_CATEGORY_HINTS):
        return True

    for kw in IT_KEYWORDS:
        pattern = r"\b" + re.escape(kw.strip()) + r"\b"
        if re.search(pattern, title):
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
        f"NEW {job['title']}\n"
        f"Company: {job['company']}\n"
        f"Location: {job['location']}\n"
        f"Source: {source}\n"
        f"Link: {job['url']}"
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
]


def gather_all_jobs():
    all_jobs = []
    for name, fetch in FETCHERS:
        try:
            portal_jobs = fetch()
            print(f"[{name}] fetched {len(portal_jobs)} jobs")
            all_jobs.extend(portal_jobs)
        except Exception as e:
            print(f"[{name}] FAILED: {e}")
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
```

> Note: emoji were removed from the message text in this saved copy to keep the
> file plain-text safe. If you want the emoji version, the messages were:
> `🆕 title`, `🏢 company`, `📍 location`, `🌐 source`, `🔗 url`.

### 3.4 `requirements.txt`

```
requests
beautifulsoup4
```

### 3.5 `.gitignore`

```
.env
__pycache__/
*.pyc
```

(Note: `seen.txt` is intentionally NOT ignored — it must be committed so the
cloud remembers seen jobs between runs.)

### 3.6 `.github/workflows/bot.yml` — the scheduler

```yaml
name: Job Notifier Bot

on:
  schedule:
    - cron: "*/30 * * * *"     # every 30 minutes
  workflow_dispatch:            # lets you run it manually too

jobs:
  run-bot:
    runs-on: ubuntu-latest
    steps:
      - name: Get the code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install libraries
        run: pip install -r requirements.txt

      - name: Run the bot
        env:
          BOT_TOKEN: ${{ secrets.BOT_TOKEN }}
          CHAT_ID: ${{ secrets.CHAT_ID }}
        run: python bot.py

      - name: Save seen.txt back to the repo
        run: |
          git config user.name "github-actions"
          git config user.email "actions@github.com"
          git add seen.txt
          git commit -m "Update seen jobs" || echo "No changes to commit"
          git push
```

---

## 4. Key setup facts (so you don't have to rediscover them)

- **On Windows, use `py` not `python`**, and `py -m pip install X` instead of
  `pip install X`.
- **Secrets** (`BOT_TOKEN`, `CHAT_ID`) live in **GitHub → repo Settings →
  Secrets and variables → Actions**, never in the code. Your code reads them via
  `os.environ[...]`.
- **Chat ID** never changes (currently your personal chat). The **token** changes
  only if you revoke it in BotFather — if so, update the `BOT_TOKEN` secret.
- **Workflow permissions** must be **"Read and write"** (repo Settings → Actions
  → General) or the "Save seen.txt" step can't push.
- **To test locally** (PowerShell), set the env vars in the same terminal first:
  ```
  $env:BOT_TOKEN="your_token"
  $env:CHAT_ID="your_chat_id"
  py bot.py
  ```
- **GitHub pauses the schedule after 60 days of repo inactivity.** Any commit or
  a manual "Run workflow" wakes it back up.

---

## 5. HOW TO ADD A NEW JOB PORTAL

This is the main thing you wanted for future work. Because of the clean design,
adding a portal is: **write one new fetcher file, add one line to `bot.py`.**
Nothing else changes — the filter, memory, Telegram, and schedule all stay the
same.

### Step-by-step

**1. Investigate the portal** (use the decision procedure in section 2).
Open the site, use browser DevTools (F12) → Network tab, and figure out whether
it's RSS, a hidden JSON API, or server-rendered HTML.

**2. Write a fetcher file** named after the portal, e.g. `jobaxle.py`. It must
have a `get_jobs()` function that returns a list of dicts in **exactly this
shape** (same as the others):

```python
{
    "id":         "jobaxle-12345",   # UNIQUE, prefixed with the portal name
    "title":      "Python Developer",
    "company":    "Some Company",
    "location":   "Kathmandu",
    "url":        "https://www.jobaxle.com/job/...",
    "posted":     "2026-08-08",      # or "" if the site doesn't show it
    "categories": ["IT", "Full Time"],  # used by the filter
    "level":      "Mid Level",       # optional
}
```

The **`id` must be unique and prefixed** (like `"jobaxle-" + number`) so it never
clashes with merojob's or kumarijob's IDs in `seen.txt`.

**Template for an API-based portal:**

```python
import requests

API_URL = "https://api.EXAMPLE.com/jobs/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 ...",
    "Accept": "application/json",
    # add Origin/Referer if the API is picky (like merojob was)
}


def get_jobs(page_size=30):
    resp = requests.get(API_URL, params={"page_size": page_size},
                        headers=HEADERS, timeout=20)
    resp.raise_for_status()
    data = resp.json()

    jobs = []
    for item in data.get("results", []):   # adjust key to match the API
        jobs.append({
            "id": "example-" + str(item["id"]),
            "title": item.get("title", ""),
            "company": item.get("company_name", "Unknown company"),
            "location": item.get("location", ""),
            "url": item.get("url", ""),
            "posted": item.get("posted_date", ""),
            "categories": item.get("categories", []),
            "level": item.get("level", ""),
        })
    return jobs
```

**Template for an HTML-scraping portal:**

```python
import requests
from bs4 import BeautifulSoup

SEARCH_URL = "https://www.EXAMPLE.com/jobs"
HEADERS = {"User-Agent": "Mozilla/5.0 ...", "Accept": "text/html"}


def get_jobs(page_size=None):
    resp = requests.get(SEARCH_URL, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    jobs = []
    for card in soup.select("CARD_SELECTOR"):        # find via Inspect
        title_el = card.select_one("TITLE_SELECTOR")
        link_el = card.select_one("a")
        if not title_el or not link_el:
            continue
        url = link_el.get("href", "")
        jobs.append({
            "id": "example-" + url.rstrip("/").split("/")[-1],
            "title": title_el.get_text(strip=True),
            "company": "",     # fill from the card
            "location": "",    # fill from the card
            "url": url,
            "posted": "",
            "categories": [],
            "level": "",
        })
    return jobs
```

**3. Test the new fetcher on its own** before wiring it in:
```
py jobaxle.py    # add an `if __name__ == "__main__":` block that prints jobs
```
Confirm it prints real jobs with correct fields.

**4. Wire it into `bot.py`** — just two small edits:

At the top with the other imports:
```python
import jobaxle
```

In the `FETCHERS` list, add one line:
```python
FETCHERS = [
    ("merojob", merojob.get_jobs),
    ("kumarijob", kumari.get_jobs),
    ("jobaxle", jobaxle.get_jobs),     # <-- new
]
```

That's it. The filter, seen-memory, Telegram, and schedule automatically apply to
the new portal too.

**5. Push to GitHub:**
```
git add .
git commit -m "Add jobaxle portal"
git push
```
The next scheduled run (or a manual "Run workflow") picks it up.

### Nepali portals you might add next
jobaxle.com, jobsnepal.com, ramrojob.com, froxjob.com, merorojgari.com,
kantipurjob.com. Each just needs its own fetcher via the same method.

---

## 6. OTHER THINGS YOU CAN CUSTOMIZE

**Change how often it runs** — edit the cron line in `bot.yml`:
- `"*/15 * * * *"` = every 15 minutes
- `"0 * * * *"` = every hour (on the hour)
- `"*/30 9-18 * * *"` = every 30 min, only 9am-6pm (UTC — note timezone!)
  (GitHub cron uses UTC. Nepal is UTC+5:45, so adjust hours accordingly.)

**Tune the filter** — edit `IT_KEYWORDS` / `IT_CATEGORY_HINTS` in `bot.py`.
Add words to catch more, remove words to reduce false positives. The filter uses
whole-word matching so short words won't hide inside unrelated words.

**Make separate filters for different needs** — e.g. a `wanted_it()` and a
`wanted_finance()` — and send them to different Telegram chats/channels.

**Nicer messages** — edit the `send_to_telegram()` text. Telegram supports
basic formatting if you add `"parse_mode": "HTML"` or `"Markdown"` to the POST
data and format the text accordingly.

**Widen kumarijob coverage** — it currently grabs the ~8 featured "card__search"
cards. To get more jobs, also parse the other card layout (`div.cardone` /
`job-card-desktop`) seen in the page, or fetch multiple pages
(`?sort=newest&page=2`, etc.).

**Missing older jobs?** — merojob's fetcher scans the newest `page_size=30`. If
lots post between runs, raise `page_size` or loop through pages.

---

## 7. QUICK TROUBLESHOOTING

- **Bot went silent for weeks** → GitHub paused the schedule (60-day inactivity).
  Make any commit or click "Run workflow" to wake it.
- **A workflow run is red** → Actions tab → click the run → click the red step →
  read the error. Common causes: a secret name typo, a portal changed its
  HTML/API (that fetcher returns 0 or errors — but `try/except` keeps others
  working), or a YAML indentation issue in `bot.yml`.
- **Getting duplicate messages** → `seen.txt` isn't persisting. Check the "Save
  seen.txt" step is green and that workflow permissions are "Read and write".
- **Telegram 401 Unauthorized** → the `BOT_TOKEN` secret is wrong or the token
  was revoked. Update the secret with the current token.
- **A portal stopped returning jobs** → that site likely changed its structure.
  Re-run the investigation (section 2) and update that fetcher's selectors/URL.
  The other portals keep working meanwhile.

---

## 8. THE MENTAL MODEL TO REMEMBER

Every bot like this is the same five pieces:

1. **Fetch** — get data from a source (API / scrape / RSS). One adapter per source.
2. **Filter** — keep only what you care about.
3. **Notify** — send it somewhere (Telegram / email / etc.).
4. **Remember** — track what you've already sent so you don't repeat.
5. **Schedule** — run it automatically on a timer (GitHub Actions cron).

You now know all five. This same skeleton works for price-drop alerts, news
monitors, restock notifiers, deadline reminders — swap the fetcher and filter,
keep the rest.

---

*Project repo: github.com/bishalzz/Job-Identifier-bot*
*Built as a first coding project — fetch, filter, notify, remember, schedule.*