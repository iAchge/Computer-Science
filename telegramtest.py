import requests

TELEGRAM_BOT_TOKEN = "8295131851:AAEGTotKaTzIvAxqxcNYk90zNOFx12vVNfk"
TELEGRAM_CHAT_ID = "8428261562"

url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
data = {
	"chat_id": 8428261562,
	"text": "Testnachricht vom Raspberry Pi (telegram_test.py)",
}

response = requests.post(url, json=data)
print("Status", response.status_code)
print("Antwort", response.text)
