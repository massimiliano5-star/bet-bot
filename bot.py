import requests
import time
import sys

def log(msg):
    print(msg, flush=True)

# --- CONFIGURAZIONE ---
API_KEY = "TUA_API_KEY"
TOKEN = "TUO_TOKEN"
CHAT_ID = "TUO_ID"

log("🚀 SCANNER VERSIONE 3.0 AVVIATO...")

def scansiona():
    log("🔍 Analisi mercati in corso...")
    # URL più specifico per evitare risposte troppo pesanti
    url = "https://the-odds-api.com" # Esempio: Premier League (cambieremo dopo)
    # Per scansionare tutto il calcio in modo sicuro:
    url_all = "https://the-odds-api.com"
    
    params = {
        'apiKey': API_KEY,
        'regions': 'eu',
        'markets': 'h2h,totals',
        'oddsFormat': 'decimal'
    }
    
    try:
        r = requests.get(url_all, params=params, timeout=30)
        
        # Se l'API non risponde 200, scriviamo perché
        if r.status_code != 200:
            log(f"❌ Errore API {r.status_code}: {r.text}")
            return

        # CONTROLLO JSON (Qui risolviamo l'errore char 0)
        try:
            data = r.json()
        except Exception:
            log("⚠️ Risposta API non valida (non è JSON). Salto questo giro.")
            return

        counter = 0
        for match in data:
            home = match.get('home_team')
            away = match.get('away_team')
            
            for bookie in match.get('bookmakers', []):
                for market in bookie.get('markets', []):
                    for out in market.get('outcomes', []):
                        if 1.20 <= out['price'] <= 1.50:
                            msg = f"💎 **SAFE BET**\n⚽ {home} - {away}\n🎯 {out['name']} @{out['price']}\n🏛️ {bookie['title']}"
                            requests.post(f"https://telegram.org{TOKEN}/sendMessage", 
                                          json={"chat_id": CHAT_ID, "text": msg})
                            counter += 1
        
        log(f"✅ Scansione completata. Segnali: {counter}")

    except Exception as e:
        log(f"⚠️ Errore tecnico: {e}")

while True:
    scansiona()
    log("💤 Pausa 30 min...")
    time.sleep(1800)
