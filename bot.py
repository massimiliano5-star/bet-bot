import requests
import csv
import time
import datetime
import os
import math

# ================= CONFIG =================
ODDS_API_KEY = "f0eaec5e8d2b7e2c0598b311b9e9aa32"
FOOTBALL_API_KEY = "50c72696adfffd60c9540455af3b7f9a"
TOKEN = "8649464893:AAHr0VkMebISJSqa-TKV0XIZxbZPjJ7LzyU"
CHAT_ID = "545852688"

BANKROLL_BASE = 50

TRACK_FILE = "track.csv"
MAX_POSITIONS = 3
MAX_DAILY_LOSS = 0.15  # 15%

open_positions = []

# ================= INIT =================
if not os.path.exists(TRACK_FILE):
    with open(TRACK_FILE, "w", newline="") as f:
        csv.writer(f).writerow(["time","match","quota","stake","result","profit"])

# ================= TELEGRAM =================
def send(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": msg}
        )
    except:
        pass

# ================= BANKROLL =================
def bankroll():
    profit = 0
    try:
        with open(TRACK_FILE) as f:
            for r in csv.DictReader(f):
                profit += float(r["profit"])
    except:
        pass
    return BANKROLL_BASE + profit

# ================= METRICS =================
def metrics(window=50):
    try:
        with open(TRACK_FILE) as f:
            rows = list(csv.DictReader(f))[-window:]

        wins = sum(1 for r in rows if r["result"] == "WIN")
        total = len(rows)
        profit = sum(float(r["profit"]) for r in rows)

        return (wins/total if total else 0), profit
    except:
        return 0, 0

def drawdown():
    return BANKROLL_BASE - bankroll()

# ================= RISK ENGINE =================
def risk_check():
    _, profit = metrics()

    if profit < -BANKROLL_BASE * MAX_DAILY_LOSS:
        return "STOP"

    if bankroll() < BANKROLL_BASE * 0.5:
        return "STOP"

    return "OK"

# ================= MODELS =================
def momentum(h, a):
    try:
        return (
            h["shots_on_goal"]*3 + h["dangerous_attacks"]*1.5
        ) / (a["shots_on_goal"]*3 + a["dangerous_attacks"]*1.5 + 1)
    except:
        return 0.5

def value_model(q):
    return (1 / q) * 1.08

def ensemble(m, v, ai):
    return m*0.4 + v*0.3 + ai*0.3

# ================= AI SIMPLE =================
def ai_model(features):
    return sum(features) / (len(features)+1) * 0.01

# ================= FEATURES =================
def features(h, a, minute, quota):
    try:
        return [
            h["shots_on_goal"] - a["shots_on_goal"],
            h["dangerous_attacks"] - a["dangerous_attacks"],
            int(h["possession"].replace("%","")) - int(a["possession"].replace("%","")),
            minute,
            quota
        ]
    except:
        return None

# ================= STAKE =================
def stake(prob, quota):
    edge = prob - (1/quota)
    if edge <= 0:
        return 0

    k = min(edge * 2, 0.05)
    return bankroll() * k

# ================= API =================
def get_matches():
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
    headers = {
        "X-RapidAPI-Key": FOOTBALL_API_KEY,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }
    params = {"live": "all"}

    try:
        return requests.get(url, headers=headers, params=params, timeout=10).json().get("response", [])
    except:
        return []

def get_odds():
    url = "https://api.the-odds-api.com/v4/sports/soccer/odds/"
    params = {"apiKey": ODDS_API_KEY,"regions":"eu","markets":"h2h"}

    try:
        return requests.get(url, params=params, timeout=10).json()
    except:
        return []

# ================= CORE ENGINE =================
def find_signals():
    matches = get_matches()
    odds = get_odds()

    signals = []

    for m in matches:
        try:
            minute = m["fixture"]["status"]["elapsed"]
            if not minute or minute < 60 or minute > 82:
                continue

            stats = m.get("statistics")
            if not stats:
                continue

            h, a = stats[0], stats[1]

            for o in odds:
                if m["teams"]["home"]["name"].lower() in o.get("home_team","").lower():

                    if not o.get("bookmakers"):
                        continue

                    for out in o["bookmakers"][0]["markets"][0]["outcomes"]:
                        q = out["price"]

                        f = features(h,a,minute,q)
                        if not f:
                            continue

                        ai = ai_model(f)
                        m1 = momentum(h,a)
                        v1 = value_model(q)

                        prob = ensemble(m1,v1,ai)
                        edge = prob - (1/q)

                        if edge > 0.12:
                            signals.append({
                                "team": out["name"],
                                "quota": q,
                                "prob": prob,
                                "edge": edge,
                                "minute": minute,
                                "match": f"{m['teams']['home']['name']} vs {m['teams']['away']['name']}"
                            })

        except:
            continue

    return sorted(signals, key=lambda x: x["edge"], reverse=True)[:MAX_POSITIONS]

# ================= EXECUTION =================
def run():
    send("🏦 INSTITUTIONAL FINAL SYSTEM ONLINE")

    while True:
        try:
            if risk_check() == "STOP":
                send("🛑 RISK SYSTEM ACTIVATED")
                time.sleep(3600)
                continue

            signals = find_signals()

            for s in signals:
                st = stake(s["prob"], s["quota"])

                if st <= 0:
                    continue

                open_positions.append(st)

                send(
                    f"🏦 SIGNAL\n{s['match']}\n{s['team']}\n"
                    f"⏱ {s['minute']}\nQuota: {s['quota']}\n"
                    f"Edge: {round(s['edge'],2)}\nStake: {round(st,2)}€"
                )

            time.sleep(60)

        except Exception as e:
            print(e)
            time.sleep(30)

run()
