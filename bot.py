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

FILE = "tracking.csv"
LAST_UPDATE_ID = None

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

# ===== STAKE DINAMICO =====
def calc_stake():
    bank = bankroll()

    if bank < 60:
        perc = 0.03
    elif bank < 100:
        perc = 0.04
    else:
        perc = 0.05

    return round(bank * perc, 2)

# ===== TRACK =====
ultima_bet = None

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

# ===== ANALISI PRO =====
def analizza():
    url = f"https://api.the-odds-api.com/v4/sports/soccer/odds/"
    params = {
        "apiKey": API_KEY,
        "regions": "eu",
        "markets": "h2h",
        "oddsFormat": "decimal"
    }

    best = None
    best_score = 0

    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()

        for m in data:
            try:
                odds = m["bookmakers"][0]["markets"][0]["outcomes"]

                t1, t2 = odds[0], odds[1]
                q1, q2 = t1["price"], t2["price"]

                if q1 < q2:
                    team, quota, opp = t1["name"], q1, q2
                else:
                    team, quota, opp = t2["name"], q2, q1

                # FILTRO ULTRA
                if 1.20 <= quota <= 1.50 and opp >= 3.2:

                    score = (opp - quota) * (1.6 - quota)

                    if score > best_score:
                        best_score = score
                        best = {
                            "match": f"{m['home_team']} vs {m['away_team']}",
                            "team": team,
                            "quota": quota
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

    send("🚀 BOT ELITE MAX ATTIVO")

    while True:

        # comandi telegram
        msgs = read_msgs()

        for m in msgs:
            if m == "WIN":
                salva("WIN")
            elif m == "LOSS":
                salva("LOSS")
            elif m == "STATUS":
                status()

        # nuova bet
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
                    f"🔥 BET ELITE\n"
                    f"{bet['match']}\n"
                    f"👉 {bet['team']}\n"
                    f"Quota: {bet['quota']}\n"
                    f"💰 Stake: {s}€\n\n"
                    f"Scrivi WIN / LOSS dopo"
                )

        time.sleep(60)

# ===== START =====
run()
