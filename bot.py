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

log("🚀 GLOBAL SCANNER PRO (Major & Minor Leagues) AVVIATO...")

def scansiona():
    log("🔍 Scansione mercati globali in corso...")
    
    # Endpoint che include tutti i campionati di calcio disponibili
    url = "https://the-odds-api.com"
    params = {
        'apiKey': API_KEY,
        'regions': 'eu',
        'markets': 'h2h,totals',
        'oddsFormat': 'decimal'
    }
    
    try:
        # Timeout aumentato a 40 secondi per i campionati minori (dati pesanti)
        r = requests.get(url, params=params, timeout=40)
        
        if r.status_code != 200:
            log(f"❌ Errore API {r.status_code}: {r.text}")
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
                        price = out.get('price')
                        
                        # FILTRO 1.20 - 1.50
                        if 1.20 <= price <= 1.50:
                            label = out.get('name')
                            if market['key'] == 'totals':
                                label = f"Over {out.get('point')} Gol"
                            
                            msg = (f"🌍 **GLOBAL SAFE BET**\n"
                                   f"🏆 {league}\n"
                                   f"⚽ {home} - {away}\n"
                                   f"🎯 {label} @{price}\n"
                                   f"🏛️ {bookie['title']}")
                            
                            # Invio Telegram
                            t_url = f"https://telegram.org{TOKEN}/sendMessage"
                            requests.post(t_url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
                            counter += 1
        
        log(f"✅ Scansione completata. Segnali inviati: {counter}")

    except Exception as e:
        log(f"⚠️ Errore tecnico: {e}")

# Ciclo ogni 30 minuti per non saturare i crediti
while True:
    scansiona()
    log("💤 Pausa 30 minuti...")
    time.sleep(1800)
