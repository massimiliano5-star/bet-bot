import requests
import time
import sys

def log(msg):
    print(msg)
    sys.stdout.flush()

# --- CONFIGURAZIONE ---
TOKEN = "IL_TUO_TOKEN"
CHAT_ID = "IL_TUO_CHAT_ID"
API_KEY = "LA_TUA_API_KEY"

log("🚀 AVVIO IN CORSO...")

def invia_test():
    url = f"https://telegram.org{TOKEN}/sendMessage"
    try:
        # Timeout di 10 secondi per non bloccare il bot
        r = requests.post(url, json={"chat_id": CHAT_ID, "text": "✅ BOT LIVE"}, timeout=10)
        log(f"📡 Risultato Telegram: {r.status_code}")
    except Exception as e:
        log(f"❌ Errore Connessione: {e}")

invia_test()

while True:
    log("🔍 Scansione mercati live...")
    # Qui inseriremo la logica dei gol appena il test passa
    time.sleep(60)
