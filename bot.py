import requests
import time
import datetime
import pytz
import csv
import os

# ===== CONFIG =====
API_KEY = "LA_TUA_API_KEY_ODDS"
FOOTBALL_API_KEY = "LA_TUA_API_KEY_FOOTBALL"
TOKEN = "TELEGRAM_TOKEN"
CHAT_ID = "CHAT_ID"

FILE = "tracking.csv"
LAST_UPDATE_ID = None
ultima_bet = None

# ===== INIT FILE =====
if not os.path.exists(FILE):
    with open(FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["data", "match", "quota", "stake", "esito", "profitto"])

# ===== TELEGRAM =====
def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": msg})

def read_msgs():
    global LAST_UPDATE_ID
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    res = requests.get(url).json()

    msgs = []
    for u in res["result"]:
        uid = u["update_id"]

        if LAST_UPDATE_ID is None or uid > LAST_UPDATE_ID:
            LAST_UPDATE_ID = uid
            if "message" in u:
                msgs.append(u["message"].get("text", "").upper())

    return msgs

# ===== TIME =====
def now():
    tz = pytz.timezone("Europe/Rome")
    return datetime.datetime.now(tz)

# ===== BANKROLL =====
def bankroll():
    profit = 0
    with open(FILE, "r") as f:
        for row in csv.DictReader(f):
            profit += float(row["profitto"])
    return 50 + profit

# ===== STAKE SAFE =====
def calc_stake():
    bank = bankroll()

    if bank < 60:
        perc = 0.02
    elif bank < 100:
        perc = 0.03
    else:
        perc = 0.04

    return round(bank * perc, 2)

# ===== TRACK =====
def salva(esito):
    global ultima_bet

    if not ultima_bet:
        return

    q = ultima_bet["quota"]
    s = ultima_bet["stake"]
    match = ultima_bet["match"]

    profit = s * (q - 1) if esito == "WIN" else -s

    with open(FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([now(), match, q, s, esito, profit])

    send(f"📊 {esito}\n💰 {round(profit,2)}€\n🏦 Bank: {round(bankroll(),2)}€")

    ultima_bet = None

# ===== PRENDI STATISTICHE REALI =====
def get_team_stats(team_name):
    try:
        url = "https://api.football-data.org/v4/teams"
        headers = {"X-Auth-Token": FOOTBALL_API_KEY}
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()

        # ⚠️ semplificato (serve mapping vero team → id)
        for t in data["teams"]:
            if team_name.lower() in t["name"].lower():
                team_id = t["id"]

                # ultime partite
                url2 = f"https://api.football-data.org/v4/teams/{team_id}/matches?limit=5"
                r2 = requests.get(url2, headers=headers, timeout=10)
                matches = r2.json()["matches"]

                wins = 0
                goals_for = 0
                goals_against = 0

                for m in matches:
                    if m["score"]["winner"] == "HOME_TEAM":
                        wins += 1
                    goals_for += m["score"]["fullTime"]["home"] or 0
                    goals_against += m["score"]["fullTime"]["away"] or 0

                form = wins / 5
                attack = goals_for / 5
                defense = goals_against / 5

                return form, attack, defense

    except:
        pass

    return None, None, None

# ===== ANALISI COMPLETA =====
def analizza():
    url = f"https://api.the-odds-api.com/v4/sports/soccer/odds/"
    params = {
        "apiKey": API_KEY,
        "regions": "eu",
        "markets": "h2h",
        "oddsFormat": "decimal"
    }

    best = None
    best_ev = 0

    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()

        for m in data:
            try:
                odds = m["bookmakers"][0]["markets"][0]["outcomes"]

                t1, t2 = odds[0], odds[1]
                q1, q2 = t1["price"], t2["price"]

                if q1 < q2:
                    team, quota, opp, opponent = t1["name"], q1, q2, t2["name"]
                else:
                    team, quota, opp, opponent = t2["name"], q2, q1, t1["name"]

                # ===== FILTRO QUOTA =====
                if not (1.20 <= quota <= 1.45):
                    continue

                if opp < 3.0:
                    continue

                # ===== DATI REALI =====
                tf, ta, td = get_team_stats(team)
                of, oa, od = get_team_stats(opponent)

                if None in (tf, ta, td, of, oa, od):
                    continue

                # ===== MODELLO STATISTICO =====
                strength = (tf * 2 + ta) - (of * 2 + od)

                if strength < 1.2:
                    continue

                # ===== PROBABILITÀ STIMATA =====
                prob = min(max(0.5 + (strength / 4), 0), 0.9)

                # ===== VALUE BETTING =====
                ev = (prob * quota) - 1

                if ev < 0.05:
                    continue

                # ===== ANTI-RISCHIO =====
                if quota < 1.30 and strength < 1.8:
                    continue

                if ev > best_ev:
                    best_ev = ev
                    best = {
                        "match": f"{m['home_team']} vs {m['away_team']}",
                        "team": team,
                        "quota": quota,
                        "ev": round(ev, 3),
                        "prob": round(prob, 2)
                    }

            except:
                continue

    except:
        return None

    return best

# ===== STATUS =====
def status():
    send(f"📊 BANKROLL: {round(bankroll(),2)}€")

# ===== LOOP =====
def run():
    global ultima_bet

    send("🚀 BOT AVANZATO ATTIVO")

    while True:

        msgs = read_msgs()

        for m in msgs:
            if m == "WIN":
                salva("WIN")
            elif m == "LOSS":
                salva("LOSS")
            elif m == "STATUS":
                status()

        if ultima_bet is None:
            bet = analizza()

            if bet:
                s = calc_stake()

                ultima_bet = {
                    "match": bet["match"],
                    "quota": bet["quota"],
                    "stake": s
                }

                send(
                    f"🔥 BET SELEZIONATA\n"
                    f"{bet['match']}\n"
                    f"👉 {bet['team']}\n"
                    f"Quota: {bet['quota']}\n"
                    f"📊 Prob: {bet['prob']}\n"
                    f"💰 EV: {bet['ev']}\n"
                    f"💸 Stake: {s}€\n\n"
                    f"Scrivi WIN / LOSS"
                )

        time.sleep(60)

# ===== START =====
run()
