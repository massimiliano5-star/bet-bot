import requests
import time
import sys

def log(msg):
    print(msg)
    sys.stdout.flush()

# --- CONFIGURAZIONE ---
# Incolla il token e l'ID ESATTAMENTE tra le virgolette
TOKEN = "7917812030:AAEl7fOa_W_C977vjD_A_n9y8" # ESEMPIO: incolla il tuo qui
CHAT_ID = "IL_TUO_ID" 
API_KEY = "LA_TUA_API_KEY"

log("🚀 AVVIO IN CORSO...")

def invia_test():
    # URL costruito in modo sicuro
    url = f"https://telegram.org{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": "✅ BOT COLLEGATO CORRETTAMENTE!"}
    
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            log("📡 Connessione Telegram stabilita!")
        else:
            log(f"❌ Errore Telegram: {r.status_code} - {r.text}")
    except Exception as e:
        log(f"⚠️ Errore critico: {e}")

invia_test()

while True:
    log("🔍 Scansione mercati live...")
    # Qui aggiungeremo la logica scommesse appena il test passa
    time.sleep(60)
