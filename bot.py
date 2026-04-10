import requests
import time
import datetime
import pytz

# ===== CONFIG =====
API_KEY = "LA_TUA_API_KEY"
TOKEN = "IL_TUO_TELEGRAM_TOKEN"
CHAT_ID = "IL_TUO_CHAT_ID"

MAX_BET_GIORNO = 2

# ===== LOG =====
def log(msg):
    print(msg, flush=True)

# ===== TELEGRAM =====
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": CHAT_ID,
        "text": msg
    })

# ===== ORARIO =====
def è_orario_di_lavoro():
    tz = pytz.timezone('Europe/Rome')
    ora = datetime.datetime.now(tz).hour
    return 8 <= ora <= 23

# ===== CAMPIONATI =====
CATEGORIE = [
    "soccer_epl", "soccer_italy_serie_a", "soccer_spain_la_liga",
    "soccer_germany_bundesliga", "soccer_france_ligue_1",
    "soccer_uefa_champs_league"
]

# ===== ANALISI MIGLIORATA =====
def analizza_lega(sport_key):
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/"
    
    params = {
        'apiKey': API_KEY,
        'regions': 'eu',
        'markets': 'h2h',
        'oddsFormat': 'decimal'
    }

    risultati = []

    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code != 200:
            return []

        data = r.json()

        for match in data:
            try:
                odds = match['bookmakers'][0]['markets'][0]['outcomes']

                if len(odds) < 2:
                    continue

                t1 = odds[0]
                t2 = odds[1]

                q1 = t1['price']
                q2 = t2['price']

                # favorita reale
                if q1 < q2:
                    favorita = t1['name']
                    quota = q1
                    sfavorita = q2
                else:
                    favorita = t2['name']
                    quota = q2
                    sfavorita = q1

                # ===== FILTRO PRO =====
                if 1.20 <= quota <= 1.50:
                    if sfavorita >= 3.00:  # grande differenza reale
                        score = sfavorita - quota  # qualità bet

                        risultati.append({
                            "match": f"{match['home_team']} vs {match['away_team']}",
                            "team": favorita,
                            "quota": quota,
                            "score": score
                        })

            except:
                continue

    except:
        return []

    return risultati

# ===== SELEZIONE TOP =====
def seleziona_top_bet(tutte_le_bet):
    # ordina per qualità (differenza quota)
    tutte_le_bet.sort(key=lambda x: x['score'], reverse=True)

    return tutte_le_bet[:MAX_BET_GIORNO]

# ===== LOOP =====
def run_bot():
    ultimo_giorno = None

    while True:
        if è_orario_di_lavoro():
            oggi = datetime.date.today()

            # manda solo una volta al giorno
            if oggi != ultimo_giorno:

                log("🔍 Analisi giornaliera...")

                tutte_le_bet = []

                for lega in CATEGORIE:
                    bets = analizza_lega(lega)
                    tutte_le_bet.extend(bets)
                    time.sleep(1)

                top_bets = seleziona_top_bet(tutte_le_bet)

                if top_bets:
                    send_telegram("🔥 TOP 2 BET DEL GIORNO 🔥")

                    for b in top_bets:
                        msg = (
                            f"\n⚽ {b['match']}\n"
                            f"👉 {b['team']}\n"
                            f"💰 Quota: {b['quota']}"
                        )
                        send_telegram(msg)
                else:
                    send_telegram("❌ Nessuna bet sicura trovata oggi")

                ultimo_giorno = oggi

            time.sleep(1800)  # controlla ogni 30 min

        else:
            log("🌙 Modalità notte")
            time.sleep(1800)

# ===== START =====
log("🚀 BOT PRO ATTIVO (MAX 2 BET/GIORNO)")
run_bot()
