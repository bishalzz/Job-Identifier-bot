import requests

URL = "https://api.merojob.com/api/v1/jobs/"       # ONE "jobs" — this was the fix
params = {"page": 1, "page_size": 10}              # 10 newest jobs
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
    "Origin": "https://merojob.com",               # "I'm from merojob"
    "Referer": "https://merojob.com/",
}

resp = requests.get(URL, params=params, headers=headers)
print("Status code:", resp.status_code)
print("Final URL:", resp.url)

try:
    data = resp.json()
except Exception:
    print("\nNot JSON. First 500 chars of response:")
    print(resp.text[:500])
    raise SystemExit

if isinstance(data, dict):
    print("Top-level keys:", list(data.keys()))
    results = data.get("results", [])
else:
    results = data

print("Number of jobs:", len(results))

if results:
    print("\n--- First job's fields ---")
    for key, value in results[0].items():
        text = str(value)
        if len(text) > 80:
            text = text[:80] + "..."
        print(key, "=", text)