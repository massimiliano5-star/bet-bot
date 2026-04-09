import requests
import time
import sys
import datetime
import pytz

# Forza la scrittura immediata dei log per Railway
def log(msg):
    print(msg, flush=True)

# --- CONFIGURAZIONE (Inserisci i tuoi dati qui) ---
API_KEY = "LA_TUA_API_KEY"
TOKEN = "IL_TUO_TELEGRAM_TOKEN"
CHAT_ID = "IL_TUO_CHAT_ID"

# 🌍 LISTA CAMPIONATI (Major, Minor & Global)
CATEGORIE = [
    "soccer_epl", "soccer_italy_serie_a", "soccer_italy_serie_b", "soccer_spain_la_liga", 
    "soccer_spain_segunda_division", "soccer_germany_bundesliga", "soccer_germany_bundesliga2",
    "soccer_france_ligue_1", "soccer_france_ligue_2", "soccer_netherlands_eredivisie",
    "soccer_portugal_primeira_liga", "soccer_belgium_first_division", "soccer_turkey_super_league",
    "soccer_uefa_champs_league", "soccer_uefa_europa_league", "soccer_brazil_campeonato",
    "soccer_usa_mls", "soccer_mexico_mx", "soccer_japan_j_league", "soccer_china_superleague"
]

def è_orario_di_lavoro():
    # Imposta il fuso orario italiano
    tz = pytz.timezone('Europe/Rome')
    ora_italiana = datetime.datetime.now(tz).hour
    # Il bot lavora dalle 08:00 alle 23:00
    if 8 <= ora_italiana <= 23:
        return True
    return False

def analizza_lega(sport_key):
    url = f"https://the-odds-api.com{sport_key}/odds/"
    params = {
        'apiKey': API_KEY,
        'regions': 'eu',
        'markets': 'h2h,totals',
        'oddsFormat': 'decimal'
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        if r.status_code != 200:
            return 0
        data = r.json()
        counter = 0
        for match in data:
            for bookie in match.get('bookmakers', []):
                for market in bookie.get('markets', []):
                    for out in market.get('outcomes', []):
                        price = out.get('price', 0)
                        # FILTRO QUOTA 1.20 - 1.50
                        if 1.20 <= price <= 1.50:
                            label = out.get('name')
                            if market['key'] == 'totals':
                                label = f"Over {out.get('point')} Gol"
                            
                            msg = (f"🌍 **SAFE BET FOUND**\n"
                                   f"🏆 {match['sport_title']}\n"
                                   f"⚽ {match['home_team']} - {match['away_team']}\n"
                                   f"🎯 {label} @{price}\n"
                                   f"🏛️ {bookie['title']}")
                            
                            requests.post(f"https://telegram.org{TOKEN}/sendMessage", 
                                          json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
                            counter += 1
                            time.sleep(0.5) # Protezione anti-spam Telegram
        return counter
    except:
        return 0

log("🚀 BOT AVVIATO: MODALITÀ RISPARMIO CREDITI ATTIVA")

# --- LOOP PRINCIPALE ---
while True:
    if è_orario_di_lavoro():
        log(f"🔄 Orario di lavoro ({datetime.datetime.now().strftime('%H:%M')}). Inizio scansione...")
        totale = 0
        for lega in CATEGORIE:
            totale += analizza_lega(lega)
            time.sleep(2) # Pausa per non saturare la RAM di Railway
        
        log(f"✅ Ciclo completato. Segnali: {totale}. Pausa 1 ora.")
        time.sleep(3600)
    else:
        log("🌙 Modalità notte: il bot dorme per risparmiare crediti.")
        # Ricontrolla ogni 30 minuti se è il momento di svegliarsi
        time.sleep(1800)
