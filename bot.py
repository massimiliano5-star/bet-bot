import requests
import time
import datetime
import pytz
import csv
import os

# ===== CONFIG =====
ODDS_API_KEY = "LA_TUA_ODDS_API_KEY"
FOOTBALL_API_KEY = "LA_TUA_API_FOOTBALL_KEY"
TOKEN = "IL_TUO_TELEGRAM_TOKEN"
CHAT_ID = "IL_TUO_CHAT_ID"

FILE = "tracking.csv"
LAST_UPDATE_ID = None

# ===== INIT FILE =====
if not os.path.exists(FILE):
    with open(FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["data", "match", "quota", "stake", "esito", "profitto"])

# ===== TELEGRAM =====
def send(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg})
    except:
        pass

# ===== READ MSG =====
def read_msgs():
    global LAST_UPDATE_ID

    try:
        res = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates").json()

        if not res.get("ok"):
            return []

        msgs = []

        for u in res.get("result", []):
            uid = u["update_id"]

            if LAST_UPDATE_ID is None or uid > LAST_UPDATE_ID:
                LAST_UPDATE_ID = uid
                text = u.get("message", {}).get("text", "")
                if text:
                    msgs.append(text.upper())

        return msgs

    except:
        return []

# ===== BANKROLL =====
def bankroll():
    profit = 0
    try:
        with open(FILE) as f:
            for row in csv.DictReader(f):
                profit += float(row["profitto"])
    except:
        pass
    return 50 + profit

def stake():
    return round(bankroll() * 0.04, 2)

# ===== SALVA =====
ultima_bet = None

def salva(esito):
    global ultima_bet

    if not ultima_bet:
        return

    q = ultima_bet["quota"]
    s = ultima_bet["stake"]

    profit = s * (q - 1) if esito == "WIN" else -s

    with open(FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([datetime.datetime.now(), ultima_bet["match"], q, s, esito, profit])

    send(f"📊 {esito} | 💰 {round(profit,2)}€ | 🏦 Bank: {round(bankroll(),2)}€")

    ultima_bet = None

# ===== API FOOTBALL =====
def get_matches():
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"

    headers = {
        "X-RapidAPI-Key": FOOTBALL_API_KEY,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }

    params = {
        "date": datetime.datetime.now().strftime("%Y-%m-%d")
    }

    try:
        res = requests.get(url, headers=headers, params=params)
        return res.json().get("response", [])
    except:
        return []

# ===== ODDS API =====
def get_odds():
    url = "https://api.the-odds-api.com/v4/sports/soccer/odds/"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "eu",
        "markets": "h2h"
    }

    try:
        res = requests.get(url, params=params)
        if res.status_code != 200:
            print("Errore Odds:", res.status_code)
            return []
        return res.json()
    except:
        return []

# ===== MATCHING + ANALISI =====
def analizza():
    matches = get_matches()
    odds = get_odds()

    best = None
    best_score = 0

    for m in matches:
        try:
            home = m["teams"]["home"]["name"]
            away = m["teams"]["away"]["name"]

            # trova match nelle odds
            for o in odds:
                if home in o["home_team"] and away in o["away_team"]:

                    outcomes = o["bookmakers"][0]["markets"][0]["outcomes"]

                    t1, t2 = outcomes[0], outcomes[1]
                    q1, q2 = t1["price"], t2["price"]

                    # scegli favorita
                    if q1 < q2:
                        team, quota, opp = t1["name"], q1, q2
                    else:
                        team, quota, opp = t2["name"], q2, q1

                    # FILTRO PRO
                    if 1.20 <= quota <= 1.50 and opp >= 3:

                        score = (opp - quota)

                        if score > best_score:
                            best_score = score
                            best = {
                                "match": f"{home} vs {away}",
                                "team": team,
                                "quota": quota
                            }

        except:
            continue

    return best

# ===== LOOP =====
def run():
    global ultima_bet

    send("🚀 BOT PRO DOPPIA API ATTIVO")

    while True:
        try:
            msgs = read_msgs()

            for m in msgs:
                if m == "WIN":
                    salva("WIN")
                elif m == "LOSS":
                    salva("LOSS")

            if ultima_bet is None:
                bet = analizza()

                if bet:
                    s = stake()

                    ultima_bet = {
                        "match": bet["match"],
                        "quota": bet["quota"],
                        "stake": s
                    }

                    send(
                        f"🔥 BET PRO\n{bet['match']}\n👉 {bet['team']}\nQuota: {bet['quota']}\n💰 Stake: {s}€"
                    )

            time.sleep(120)

        except Exception as e:
            print("Errore:", e)
            time.sleep(30)

# ===== START =====
run()
