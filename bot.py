import requests
import time
import sys

# Forza l'uscita dei log
def log(msg):
    print(msg)
    sys.stdout.flush()

# --- CONFIGURAZIONE ---
API_KEY = "LA_TUA_API_KEY"
TOKEN = "IL_TUO_TOKEN"
CHAT_ID = "IL_TUO_ID"

log("🚀 SCANNER PRE-MATCH (1.20-1.50) INIZIALIZZATO...")

def scansiona():
    url = "https://the-odds-api.com"
    params = {
        'apiKey': API_KEY,
        'regions': 'eu',
        'markets': 'h2h,totals',
        'oddsFormat': 'decimal'
    }
    
    try:
        log("🔍 Analisi campionati in corso...")
        r = requests.get(url, params=params, timeout=20)
        
        if r.status_code != 200:
            log(f"❌ Errore API: {r.status_code}")
            return

        matches = r.json()
        counter = 0
        
        for m in matches:
            home = m.get('home_team')
            away = m.get('away_team')
            league = m.get('sport_title')
            
            for b in m.get('bookmakers', []):
                for market in b.get('markets', []):
                    for out in market.get('outcomes', []):
                        # FILTRO QUOTA 1.20 - 1.50
                        if 1.20 <= out['price'] <= 1.50:
                            msg = (f"⚽ **QUOTA TOP**\n"
                                   f"🏆 {league}\n"
                                   f"🏟️ {home} - {away}\n"
                                   f"🎯 {out['name']} @{out['price']}\n"
                                   f"🏛️ {b['title']}")
                            
                            t_url = f"https://telegram.org{TOKEN}/sendMessage"
                            requests.post(t_url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
                            counter += 1
        
        log(f"✅ Fine scansione. Segnali inviati: {counter}")

    except Exception as e:
        log(f"⚠️ Errore tecnico: {e}")

# Ciclo ogni ora
while True:
    scansiona()
    log("💤 Prossimo controllo tra 1 ora...")
    time.sleep(3600)
