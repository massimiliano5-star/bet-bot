import requests
import time
import datetime
import csv
import os
import math

# ===== CONFIG =====
ODDS_API_KEY = "f0eaec5e8d2b7e2c0598b311b9e9aa32"
FOOTBALL_API_KEY = "50c72696adfffd60c9540455af3b7f9a"
TOKEN = "8649464893:AAHr0VkMebISJSqa-TKV0XIZxbZPjJ7LzyU"
CHAT_ID = "545852688"

TRACK_FILE = "tracking.csv"
DATASET = "dataset.csv"

BANKROLL_BASE = 50

# ===== INIT FILE =====
if not os.path.exists(TRACK_FILE):
    with open(TRACK_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["data","match","quota","stake","esito","profitto"])

if not os.path.exists(DATASET):
    with open(DATASET, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["shots_diff","att_diff","poss_diff","minute","quota","result"])

# ===== TELEGRAM =====
def send(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg})
    except:
        pass

# ===== BANKROLL =====
def bankroll():
    profit = 0
    try:
        with open(TRACK_FILE) as f:
            for r in csv.DictReader(f):
                profit += float(r["profitto"])
    except:
        pass
    return BANKROLL_BASE + profit

# ===== API =====
def get_live_matches():
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
    headers = {
        "X-RapidAPI-Key": FOOTBALL_API_KEY,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }
    params = {"live": "all"}

    try:
        res = requests.get(url, headers=headers, params=params, timeout=10)
        return res.json().get("response", [])
    except:
        return []

def get_odds():
    url = "https://api.the-odds-api.com/v4/sports/soccer/odds/"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "eu",
        "markets": "h2h"
    }

    try:
        return requests.get(url, params=params, timeout=10).json()
    except:
        return []

# ===== AI MODEL =====
weights = [0.1, 0.1, 0.05, 0.01, -0.2]

def predict(features):
    z = sum(w*f for w,f in zip(weights, features))
    return 1 / (1 + math.exp(-z))

def train():
    global weights
    lr = 0.001

    try:
        with open(DATASET) as f:
            data = list(csv.DictReader(f))

        for row in data:
            x = [
                float(row["shots_diff"]),
                float(row["att_diff"]),
                float(row["poss_diff"]),
                float(row["minute"]),
                float(row["quota"])
            ]
            y = int(row["result"])

            pred = predict(x)
            error = y - pred

            for i in range(len(weights)):
                weights[i] += lr * error * x[i]
    except:
        pass

# ===== FEATURES =====
def extract_features(home_stats, away_stats, minute, quota):
    try:
        return [
            home_stats["shots_on_goal"] - away_stats["shots_on_goal"],
            home_stats["dangerous_attacks"] - away_stats["dangerous_attacks"],
            int(home_stats["possession"].replace("%","")) - int(away_stats["possession"].replace("%","")),
            minute,
            quota
        ]
    except:
        return None

# ===== ULTRA MODEL =====
def calc_ultra_prob(home_stats, away_stats, minute):
    try:
        h = home_stats
        a = away_stats

        home_score = (h["shots_on_goal"]*3 + h["dangerous_attacks"]*1.5 + int(h["possession"].replace("%","")))
        away_score = (a["shots_on_goal"]*3 + a["dangerous_attacks"]*1.5 + int(a["possession"].replace("%","")))

        boost = 1 + (minute/90)

        home_score *= boost
        away_score *= boost

        total = home_score + away_score
        if total == 0:
            return 0,0

        return home_score/total, away_score/total
    except:
        return 0,0

# ===== VALUE =====
def value_score(quota):
    return (1 / quota) * 1.1

def combined_score(m,v,a):
    return (m*0.4 + v*0.3 + a*0.3)

# ===== KELLY =====
def kelly(prob, quota):
    b = quota - 1
    q = 1 - prob
    k = (b*prob - q) / b
    return max(0, min(k, 0.05))

# ===== RISK =====
def risk_control():
    b = bankroll()
    if b < 30:
        return "STOP"
    elif b < 45:
        return "LOW"
    return "NORMAL"

# ===== CORE =====
def find_bets():
    matches = get_live_matches()
    odds = get_odds()

    candidates = []

    for m in matches:
        try:
            minute = m["fixture"]["status"]["elapsed"]
            if minute is None or minute < 60 or minute > 82:
                continue

            stats = m.get("statistics")
            if not stats:
                continue

            home = m["teams"]["home"]["name"]
            away = m["teams"]["away"]["name"]

            home_stats = stats[0]
            away_stats = stats[1]

            if home_stats["dangerous_attacks"] + away_stats["dangerous_attacks"] < 40:
                continue

            for o in odds:
                if home.lower() in o.get("home_team","").lower():

                    if not o.get("bookmakers"):
                        continue

                    outcomes = o["bookmakers"][0]["markets"][0]["outcomes"]

                    for out in outcomes:
                        quota = out["price"]
                        team = out["name"]

                        features = extract_features(home_stats, away_stats, minute, quota)
                        if not features:
                            continue

                        prob_ai = predict(features)
                        ph, pa = calc_ultra_prob(home_stats, away_stats, minute)
                        prob_m = ph if team == home else pa
                        prob_v = value_score(quota)

                        final_prob = combined_score(prob_m, prob_v, prob_ai)
                        prob_book = 1 / quota
                        value = final_prob - prob_book

                        if value > 0.15:
                            candidates.append({
                                "team": team,
                                "quota": quota,
                                "value": value,
                                "prob": final_prob,
                                "minute": minute,
                                "features": features,
                                "match": f"{home} vs {away}"
                            })

        except:
            continue

    if not candidates:
        return None

    return sorted(candidates, key=lambda x: x["value"], reverse=True)[:2]

# ===== TRACK =====
ultima_bet = None

def save_result(esito):
    global ultima_bet

    if not ultima_bet:
        return

    q = ultima_bet["quota"]
    s = ultima_bet["stake"]

    profit = s*(q-1) if esito=="WIN" else -s

    with open(TRACK_FILE,"a",newline="") as f:
        csv.writer(f).writerow([
            datetime.datetime.now(),
            ultima_bet["match"],
            q,s,esito,profit
        ])

    with open(DATASET,"a",newline="") as f:
        csv.writer(f).writerow(ultima_bet["features"] + [1 if esito=="WIN" else 0])

    send(f"📊 {esito} | 💰 {round(profit,2)}€ | 🏦 {round(bankroll(),2)}€")

    ultima_bet = None

# ===== LOOP =====
def run():
    global ultima_bet

    send("💼 HEDGE FUND BOT ATTIVO")

    while True:
        try:
            mode = risk_control()
            if mode == "STOP":
                send("🛑 STOP DRAWNDOWN")
                time.sleep(3600)
                continue

            bets = find_bets()

            if bets:
                for b in bets:
                    stake = round(bankroll() * kelly(b["prob"], b["quota"]),2)

                    ultima_bet = {
                        "match": b["match"],
                        "quota": b["quota"],
                        "stake": stake,
                        "features": b["features"]
                    }

                    send(
                        f"💼 BET\n{b['match']}\n👉 {b['team']}\n"
                        f"⏱ {b['minute']}\nQuota: {b['quota']}\n"
                        f"📊 Prob: {round(b['prob'],2)}\n"
                        f"📈 Value: {round(b['value'],2)}\n"
                        f"💰 Stake: {stake}€"
                    )

            train()

            time.sleep(60)

        except Exception as e:
            print("Errore:", e)
            time.sleep(30)

run()
