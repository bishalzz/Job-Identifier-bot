import requests

TOKEN = "8778594474:AAHiBc9T27OAyI2YcF6GvauQWPaZVg2hD9s"

CHAT_ID = "1327235031"

response = requests.post(
    f"https://api.telegram.org/bot{TOKEN}/sendMessage",
    data={"chat_id": CHAT_ID, "text": "Hello! My job bot is alive 🎉"},
)

print(response.status_code)
print(response.json())