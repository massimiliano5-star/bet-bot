import requests
import time
import sys

# Forza la scrittura immediata dei log
def log(msg):
    print(msg, flush=True)

# --- CONFIGURAZIONE ---
API_KEY = "TUA_API_KEY"
TOKEN = "TUO_TOKEN"
CHAT_ID = "TUO_ID"

log("🚀 --- BOT IN FASE DI AVVIO ---")

def scansiona():
    log("🔍 Controllo mercati in corso...")
    url = "https://the-odds-api.com"
    params = {
        'apiKey': API_KEY,
        'regions': 'eu',
        'markets': 'h2h',
        'oddsFormat': 'decimal'
    }
    
    try:
        r = requests.get(url, params=params, timeout=20)
        log(f"📡 Risposta API: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            counter = 0
            for m in data:
                for b in m.get('bookmakers', []):
                    for mk in b.get('markets', []):
                        for out in mk.get('outcomes', []):
                            if 1.20 <= out['price'] <= 1.50:
                                t_url = f"https://telegram.org{TOKEN}/sendMessage"
                                msg = f"⚽ SAFE BET: {m['home_team']}-{m['away_team']} @{out['price']}"
                                requests.post(t_url, json={"chat_id": CHAT_ID, "text": msg})
                                counter += 1
            log(f"✅ Scansione finita. Segnali: {counter}")
        else:
            log(f"❌ Errore API: {r.text}")

    except Exception as e:
        log(f"⚠️ Errore tecnico: {e}")

# Ciclo infinito
while True:
    scansiona()
    log("💤 Pausa di 1 ora...")
    time.sleep(3600)
