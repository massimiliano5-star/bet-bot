import requests
import time
import sys

def log(msg):
    print(msg)
    sys.stdout.flush()

# --- CONFIGURAZIONE ---
# Incolla i tuoi dati ESATTAMENTE tra le virgolette
TOKEN = "7917812030:AAEl7fOa_W_C977vjD_A_n9y8" # Usa il tuo token completo qui
CHAT_ID = "6365922372" # Assicurati che sia il tuo ID numerico
API_KEY = "LA_TUA_API_KEY_DI_THE_ODDS"

log("🚀 AVVIO IN CORSO...")

def invia_test():
    # URL costruito con lo slash corretto dopo 'bot'
    url = f"https://telegram.org{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": "✅ CONNESSIONE STABILITA! Il bot è ora configurato correttamente."}
    
    try:
        r = requests.post(url, json=payload, timeout=15)
        if r.status_code == 200:
            log("📡 Telegram ha accettato il messaggio!")
        else:
            log(f"❌ Errore Telegram: {r.status_code} - {r.text}")
    except Exception as e:
        log(f"⚠️ Errore di rete: {e}")

# Eseguiamo il test subito
invia_test()

while True:
    log("🔍 Scansione mercati live in corso...")
    # Qui inseriremo la logica per i gol/corner una volta confermato il test
    time.sleep(60)
