import requests
import time

TELEGRAM_TOKEN = "INSERISCI_TOKEN"
CHAT_ID = "INSERISCI_CHAT_ID"

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

def run_bot():
    while True:
        msg = "🤖 Bot attivo! Sto cercando opportunità..."
        print(msg)
        send_telegram(msg)
        
        time.sleep(3600)  # ogni 1 ora

if __name__ == "__main__":
    run_bot()
