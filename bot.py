import requests
import time
import sys

def log(msg):
    print(msg, flush=True)

# --- CONFIGURAZIONE ---
API_KEY = "LA_TUA_API_KEY"
TOKEN = "IL_TUO_TOKEN"
CHAT_ID = "IL_TUO_ID"

log("🚀 GLOBAL SCANNER 5.0 - MODALITÀ SICURA")

def analizza_lega(sport_key):
    url = f"https://the-odds-api.com{sport_key}/odds/"
    params = {
        'apiKey': API_KEY,
        'regions': 'eu',
        'markets': 'h2h,totals',
        'oddsFormat': 'decimal'
    }
    
    try:
        r = requests.get(url, params=params, timeout=20)
        if r.status_code != 200:
            return 0

        data = r.json()
        counter = 0
        for match in data:
            for bookie in match.get('bookmakers', []):
                for market in bookie.get('markets', []):
                    for out in market.get('outcomes', []):
                        if 1.20 <= out.get('price', 0) <= 1.50:
                            msg = f"🌍 **BET**\n🏆 {match['sport_title']}\n⚽ {match['home_team']}-{match['away_team']}\n🎯 {out['name']} @{out['price']}"
                            requests.post(f"https://telegram.org{TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": msg})
                            counter += 1
        return counter
    except:
        return 0

def scansiona_mondo():
    # Lista di gruppi "sicuri" che includono campionati maggiori e minori
    categorie = ["soccer_epl", "soccer_italy_serie_a", "soccer_spain_la_liga", "soccer_germany_bundesliga", "soccer_france_ligue_1", "soccer_uefa_champs_league"]
    
    totale = 0
    for lega in categorie:
        log(f"🔍 Scansione: {lega}...")
        totale += analizza_lega(lega)
        time.sleep(2) # Pausa di sicurezza tra le leghe
    
    log(f"✅ Scansione completata. Segnali totali: {totale}")

while True:
    scansiona_mondo()
    log("💤 Pausa 1 ora per risparmio crediti...")
    time.sleep(3600)
