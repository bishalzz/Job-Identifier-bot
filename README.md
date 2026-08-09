# Job Notifier Bot — Kathmandu IT Jobs

A Telegram bot that watches **six Nepali job portals** and posts every new
**IT / networking / development** job to a public Telegram channel
([t.me/ktm_it_jobs](https://t.me/ktm_it_jobs)). It runs itself every 30 minutes
on GitHub Actions — free, and even when your computer is off.

Built from scratch as a first coding project. The pattern behind it —
**fetch → filter → dedup → notify → remember → schedule** — works for almost any
monitoring bot.

---

## What it does

- Fetches jobs from **6 portals**: merojob, kumarijob, educatenepal,
  merorojgari, hamrojobs, jobejee.
- Keeps only **IT / networking / development** jobs (keyword + category filter).
- **Deduplicates** across portals — the same job on two sites is sent once.
- **Remembers** what it already sent (no repeats), persisted across cloud runs.
- **Broadcasts** new matches to a public Telegram channel.
- Runs **automatically every 30 minutes** via GitHub Actions.

```
   every 30 min (GitHub Actions cron)
              |
              v
        bot.py  ──asks──>  6 portal fetchers (below)
              |
              |  filter to IT jobs -> dedup across portals ->
              |  skip anything already in seen.txt
              v
        Telegram channel  ──>  subscribers' phones
              |
              v
     saves seen.txt back to the repo (so it remembers next run)
```

---

## Files

**Core (needed to run):**

| File | Role |
|------|------|
| `bot.py` | The brain: combines portals, filters, dedups, notifies, remembers |
| `jobs.py` | merojob fetcher (hidden JSON API) |
| `kumari.py` | kumarijob fetcher (HTML scrape) |
| `educatenepal.py` | educatenepal fetcher (HTML scrape) |
| `merorojgari.py` | merorojgari fetcher (HTML scrape, WordPress) |
| `hamrojobs.py` | hamrojobs fetcher (HTML scrape) |
| `jobejee.py` | jobejee fetcher (HTML scrape) |
| `requirements.txt` | Python libraries (requests, beautifulsoup4) |
| `.gitignore` | keeps `.env` and caches out of the repo |
| `.github/workflows/bot.yml` | the 30-minute scheduler + saves seen.txt back |
| `seen.txt` | memory of sent jobs (IDs + title/company signatures) |

---

## How each portal is fetched

Three techniques, depending on how the site serves data:

- **merojob → hidden JSON API.** Jobs load via JavaScript from
  `https://api.merojob.com/api/v1/jobs/`. We call it directly (needs `Origin`
  and `Referer` headers set to merojob). Cleanest, most stable.
- **kumarijob / educatenepal / merorojgari / hamrojobs / jobejee → HTML scrape.**
  Jobs are in the page HTML. We fetch the page and pull job cards out with
  BeautifulSoup. Simpler, but breaks if the site redesigns (that fetcher then
  returns 0 jobs — the `try/except` keeps the others running).

**To investigate ANY new portal:**
1. RSS feed? (try `/feed`, `/rss`) → easiest.
2. Hidden JSON API? (browser F12 → Network → Fetch/XHR, reload or search, look
   for a request returning job data) → clean.
3. Jobs in the page HTML? → scrape with requests + BeautifulSoup.
4. Page HTML empty (JS-only) + no findable API → needs a real-browser tool
   (Playwright). Usually not worth it.

---

## The job format (every fetcher returns this)

Each fetcher's `get_jobs()` returns a list of dicts shaped like:

```python
{
    "id":         "portalname-12345",   # UNIQUE, prefixed with the portal name
    "title":      "Python Developer",
    "company":    "Some Company",
    "location":   "Kathmandu",
    "url":        "https://...",         # full clickable link
    "posted":     "2026-08-08",          # or "" if not available
    "categories": ["IT", "Full Time"],   # used by the filter
    "level":      "Mid Level",           # optional
}
```

`bot.py` adds a `"source"` field automatically. The `id` must be unique and
prefixed (e.g. `"jobejee-" + number`) so IDs never collide across portals.

---

## Setup facts

- **Windows:** use `py` not `python`, and `py -m pip install X` not `pip install X`.
- **Secrets** live in GitHub → repo **Settings → Secrets and variables → Actions**:
  - `BOT_TOKEN` — the Telegram bot token (from BotFather).
  - `CHAT_ID` — `@ktm_it_jobs` (the channel; note the `@`).
  The code reads these via `os.environ[...]` — never hardcoded.
- **Workflow permissions** must be **Read and write** (Settings → Actions →
  General) so the workflow can save `seen.txt` back.
- **The bot must be an admin** of the Telegram channel (with Post Messages).
- **Test locally** (PowerShell), set env vars in the same terminal first:
  ```
  $env:BOT_TOKEN=("your_token").Trim()
  $env:CHAT_ID="1327235031"      # your personal chat, for testing
  py bot.py
  ```
- **GitHub pauses the schedule after 60 days of repo inactivity.** Any commit or
  a manual "Run workflow" wakes it back up.

---

## Working with the repo (important!)

Because the bot **auto-commits `seen.txt` every 30 minutes**, the GitHub repo is
often *ahead* of your local copy. So when you push a change and it's rejected
("non-fast-forward"), just pull first:

```
git add <files>
git commit -m "your message"
git pull --no-edit      # download the cloud's seen.txt updates
git push
```

This pull-then-push rhythm is normal for this project.

---

## Adding a new portal (if you ever want to)

1. Investigate the portal (RSS / API / HTML — see above).
2. Write `portalname.py` with a `get_jobs()` returning the job format above
   (unique, prefixed IDs!).
3. Test it alone: `py portalname.py` — confirm it prints real jobs.
4. In `bot.py`: add `import portalname` and one line to `FETCHERS`:
   ```python
   ("portalname", portalname.get_jobs),
   ```
5. Push (with the pull-then-push rhythm).

> Note: with 6 portals you already cover most of Nepal's IT jobs. Many smaller
> sites just repost the same jobs, so more portals mostly add duplicates (which
> dedup then hides anyway). Quality > quantity at this point.

---

## Customizing

- **Filter:** edit `IT_KEYWORDS` / `IT_CATEGORY_HINTS` in `bot.py`. Whole-word
  matching is used for titles so short words don't hide inside other words.
- **Schedule:** edit the `cron` line in `bot.yml`
  (`"*/30 * * * *"` = every 30 min; `"0 * * * *"` = hourly). Cron is in UTC.
- **Message format:** edit `send_to_telegram()` in `bot.py`.
- **Dedup:** handled by `job_signature()` (normalized title+company). Catches
  obvious duplicates; won't catch cases where portals spell the company
  differently or truncate the title.

---

## Troubleshooting

- **Bot silent for weeks** → schedule paused (60-day inactivity). Commit or Run
  workflow to wake it.
- **A run is red** → Actions → click run → click the red step → read the error.
  Common: a secret name typo, a portal changed its HTML (that fetcher returns 0;
  others keep working), or YAML indentation in `bot.yml`.
- **Duplicate messages** → check the "Save seen.txt" step is green and workflow
  permissions are Read and write.
- **Nothing posts to the channel but run is green** → likely 0 new jobs right now
  (correct), OR the `CHAT_ID` secret isn't `@ktm_it_jobs` (with the `@`).
- **Telegram 401 Unauthorized** → `BOT_TOKEN` secret wrong or token revoked.
- **A portal stopped returning jobs** → it changed its structure; re-investigate
  and update that fetcher. Others keep working meanwhile.

---

## The mental model

Every bot like this is the same pieces:

1. **Fetch** — get data from sources (API / scrape / RSS). One adapter per source.
2. **Filter** — keep only what you care about.
3. **Dedup** — don't send the same thing twice.
4. **Notify** — send it somewhere (Telegram).
5. **Remember** — track what you've sent.
6. **Schedule** — run automatically (GitHub Actions cron).

Swap the fetcher and filter, keep the rest — and this becomes a price-drop
alerter, news monitor, restock notifier, whatever.

---

*Repo: github.com/bishalzz/Job-Identifier-bot · Channel: t.me/ktm_it_jobs*