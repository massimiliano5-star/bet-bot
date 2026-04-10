import requests
import time
import datetime
import pytz
import csv
import os

# ===== CONFIG =====
API_KEY = "LA_TUA_API_KEY"
TOKEN = "IL_TUO_TELEGRAM_TOKEN"
CHAT_ID = "IL_TUO_CHAT_ID"

FILE_TRACK = "tracking.csv"

# ===== INIT FILE =====
if not os.path.exists(FILE_TRACK):
    with open(FILE_TRACK, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["data", "tipo", "match", "quota", "stake", "esito", "profitto"])

# ===== TELEGRAM =====
def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": msg})

# ===== TIME =====
def now():
    tz = pytz.timezone("Europe/Rome")
    return datetime.datetime.now(tz)

# ===== BANKROLL =====
def get_bankroll():
    profit = 0
    with open(FILE_TRACK, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            profit += float(row["profitto"])
    return 50 + profit

def stake():
    return round(get_bankroll() * 0.05, 2)

# ===== TRACK =====
def salva(tipo, match, quota, stake, esito):
    profit = stake * (quota - 1) if esito == "WIN" else -stake

    with open(FILE_TRACK, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            now(),
            tipo,
            match,
            quota,
            stake,
            esito,
            profit
        ])

# ===== ANALISI =====
def analizza():
    leagues = [
        "soccer_epl",
        "soccer_italy_serie_a",
        "soccer_spain_la_liga"
    ]

    risultati = []

    for league in leagues:
        url = f"https://api.the-odds-api.com/v4/sports/{league}/odds/"
        params = {
            "apiKey": API_KEY,
            "regions": "eu",
            "markets": "h2h",
            "oddsFormat": "decimal"
        }

        try:
            r = requests.get(url, params=params, timeout=10)
            data = r.json()

            for m in data:
                odds = m["bookmakers"][0]["markets"][0]["outcomes"]

                t1, t2 = odds[0], odds[1]
                q1, q2 = t1["price"], t2["price"]

                if q1 < q2:
                    team, quota, opp = t1["name"], q1, q2
                else:
                    team, quota, opp = t2["name"], q2, q1

                if 1.20 <= quota <= 1.50 and opp >= 3:
                    score = opp - quota

                    risultati.append({
                        "match": f"{m['home_team']} vs {m['away_team']}",
                        "team": team,
                        "quota": quota,
                        "score": score
                    })

        except:
            continue

    risultati.sort(key=lambda x: x["score"], reverse=True)
    return risultati[:2]

# ===== LIVE =====
def live():
    # simulazione migliorata logica live
    return [{
        "match": "LIVE 0-0 60min",
        "bet": "Over 0.5",
        "quota": 1.30
    }]

# ===== REPORT =====
def report():
    bank = get_bankroll()
    send(f"📊 BANKROLL ATTUALE: {round(bank,2)}€")

# ===== LOOP =====
def run():
    ultimo_giorno = None

    while True:
        oggi = now().date()

        if oggi != ultimo_giorno:

            bets = analizza()
            s = stake()

            send(f"🔥 BET ELITE\n💰 Stake: {s}€")

            for b in bets:
                send(
                    f"\n⚽ {b['match']}\n"
                    f"👉 {b['team']}\n"
                    f"Quota: {b['quota']}"
                )

            for l in live():
                send(
                    f"\n⚡ LIVE\n{l['match']}\n{l['bet']} @ {l['quota']}"
                )

            report()

            ultimo_giorno = oggi

        time.sleep(1800)

# ===== START =====
send("🚀 BOT ELITE ATTIVO")
run()
