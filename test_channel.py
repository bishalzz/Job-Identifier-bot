import os
import requests

TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

resp = requests.post(
    f"https://api.telegram.org/bot{TOKEN}/sendMessage",
    data={"chat_id": CHAT_ID, "text": "✅ Channel test — if you see this, the channel is working!"},
    timeout=20,
)
print("Status:", resp.status_code)
print(resp.json())