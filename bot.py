import requests
import time
import sys

# Forza l'output immediato per evitare il blocco "Starting Container"
def log(msg):
    print(msg, flush=True)

# --- CONFIGURAZIONE ---
API_KEY = "LA_TUA_API_KEY"
TOKEN = "IL_TUO_TOKEN"
CHAT_ID = "IL_TUO_ID"

log("🚀 GLOBAL SCANNER 4.0 - AVVIO IN CORSO...")

def scansiona():
    # Usiamo l'endpoint 'upcoming' che è il più leggero per i campionati minori
    url = "https://the-odds-api.com"
    params = {
        'apiKey': API_KEY,
        'regions': 'eu',
        'markets': 'h2h,totals',
        'oddsFormat': 'decimal'
    }
    
    try:
        log("🔍 Scansione mercati mondiali...")
        # Timeout corto per non far bloccare il container
        r = requests.get(url, params=params, timeout=15)
        
        if r.status_code != 200:
            log(f"❌ Errore API: {r.status_code}")
            return

        data = r.json()
        counter = 0
        
        for match in data:
            home = match.get('home_team')
            away = match.get('away_team')
            league = match.get('sport_title')
            
            for bookie in match.get('bookmakers', []):
                for market in bookie.get('markets', []):
                    for out in market.get('outcomes', []):
                        price = out.get('price', 0)
                        
                        # FILTRO QUOTA 1.20 - 1.50
                        if 1.20 <= price <= 1.50:
                            label = out.get('name')
                            if market['key'] == 'totals':
                                label = f"Over {out.get('point')} Gol"
                            
                            msg = f"🌍 **GLOBAL SAFE**\n🏆 {league}\n⚽ {home}-{away}\n🎯 {label} @{price}"
                            
                            # Invio immediato
                            requests.post(f"https://telegram.org{TOKEN}/sendMessage", 
                                          json={"chat_id": CHAT_ID, "text": msg})
                            counter += 1
                            # Piccola pausa per non saturare la banda di Railway
                            time.sleep(0.5)

        log(f"✅ Scansione completata. Segnali: {counter}")

    except Exception as e:
        log(f"⚠️ Errore: {e}")

# --- LOOP ---
while True:
    scansiona()
    log("💤 Pausa 30 min...")
    time.sleep(1800)
