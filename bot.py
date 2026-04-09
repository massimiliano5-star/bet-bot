import requests
import time
import sys

# Forza l'output immediato per Railway
def log(msg):
    print(msg, flush=True)

# --- CONFIGURAZIONE ---
API_KEY = "TUA_API_KEY"
TOKEN = "TUO_TOKEN"
CHAT_ID = "TUO_ID"

# 🌍 LISTA COMPLETA OTTIMIZZATA
CATEGORIE = [
    "soccer_epl", "soccer_italy_serie_a", "soccer_italy_serie_b", "soccer_spain_la_liga", 
    "soccer_spain_segunda_division", "soccer_germany_bundesliga", "soccer_germany_bundesliga2",
    "soccer_france_ligue_1", "soccer_france_ligue_2", "soccer_netherlands_eredivisie",
    "soccer_portugal_primeira_liga", "soccer_belgium_first_division", "soccer_turkey_super_league",
    "soccer_uefa_champs_league", "soccer_uefa_europa_league", "soccer_brazil_campeonato",
    "soccer_usa_mls", "soccer_mexico_mx", "soccer_japan_j_league", "soccer_china_superleague"
]

def analizza_lega(sport_key):
    url = f"https://the-odds-api.com{sport_key}/odds/"
    params = {'apiKey': API_KEY, 'regions': 'eu', 'markets': 'h2h,totals', 'oddsFormat': 'decimal'}
    try:
        r = requests.get(url, params=params, timeout=15)
        if r.status_code != 200: return 0
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
    except: return 0

log("🚀 BOT AVVIATO CON SUCCESSO!")

# Ciclo principale
while True:
    log(f"🔄 Inizio scansione globale ({len(CATEGORIE)} leghe)...")
    totale = 0
    for lega in CATEGORIE:
        totale += analizza_lega(lega)
        time.sleep(2) # Pausa salva-memoria
    
    log(f"✅ Fine ciclo. Segnali inviati: {totale}")
    log("💤 Pausa 1 ora...")
    time.sleep(3600)
