import requests
import time
import datetime
import csv
import os
import math
import json

# ================= CONFIG =================
ODDS_API_KEY = "f0eaec5e8d2b7e2c0598b311b9e9aa32"
FOOTBALL_API_KEY = "50c72696adfffd60c9540455af3b7f9a"
TOKEN = "8649464893:AAHr0VkMebISJSqa-TKV0XIZxbZPjJ7LzyU"
CHAT_ID = "545852688"

BANKROLL_BASE = 50

TRACK_FILE = "tracking.csv"
DATASET = "dataset.csv"
WEIGHTS_FILE = "weights.json"

MAX_POSITIONS = 3
MAX_EXPOSURE = 0.15

open_positions = []

# ================= INIT =================
if not os.path.exists(TRACK_FILE):
    with open(TRACK_FILE, "w", newline="") as f:
        csv.writer(f).writerow(["time","match","quota","stake","esito","profit"])

if not os.path.exists(DATASET):
    with open(DATASET, "w", newline="") as f:
        csv.writer(f).writerow(["f1","f2","f3","minute","quota","result"])

# ================= WEIGHTS AI =================
def load_weights():
    if os.path.exists(WEIGHTS_FILE):
        return json.load(open(WEIGHTS_FILE))
    return [0.1, 0.1, 0.05, 0.01, -0.2]

def save_weights(w):
    with open(WEIGHTS_FILE, "w") as f:
        json.dump(w, f)

weights = load_weights()

def predict(features):
    z = sum(w*f for w,f in zip(weights, features))
    return 1 / (1 + math.exp(-z))

def self_learn(features, result):
    global weights
    lr = 0.001

    pred = predict(features)
    error = result - pred

    for i in range(len(weights)):
        weights[i] += lr * error * features[i]

    save_weights(weights)

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

        wins = sum(1 for r in rows if r["esito"] == "WIN")
        profit = sum(float(r["profit"]) for r in rows)

        total = len(rows)
        winrate = wins / total if total else 0

        return winrate, profit
    except:
        return 0, 0

def sharpe_like():
    try:
        profits = []
        with open(TRACK_FILE) as f:
            for r in csv.DictReader(f):
                profits.append(float(r["profit"]))

        if len(profits) < 5:
            return 0

        avg = sum(profits)/len(profits)
        std = (sum((x-avg)**2 for x in profits)/len(profits))**0.5

        return avg / std if std else 0
    except:
        return 0

# ================= RISK =================
def risk_check():
    bank = bankroll()
    winrate, profit = metrics()

    if profit < -bank * 0.1:
        return "STOP"

    if bank < BANKROLL_BASE * 0.6:
        return "STOP"

    return "OK"

# ================= MODELS =================
def momentum_model(h, a):
    return (
        h["shots_on_goal"]*3 + h["dangerous_attacks"]*1.5
    ) / (
        a["shots_on_goal"]*3 + a["dangerous_attacks"]*1.5 + 1
    )

def value_model(quota):
    return (1 / quota) * 1.1

def ensemble(prob_m, prob_v, prob_ai):
    return prob_m*0.35 + prob_v*0.25 + prob_ai*0.40

# ================= FEATURES =================
def extract(h, a, minute, quota):
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
def kelly(prob, quota):
    b = quota - 1
    q = 1 - prob
    k = (b*prob - q) / b
    return max(0, min(k, 0.05))

def stake(prob, quota):
    if current_exposure() > bankroll() * MAX_EXPOSURE:
        return 0
    return bankroll() * kelly(prob, quota)

# ================= EXPOSURE =================
def current_exposure():
    return sum(p["stake"] for p in open_positions)

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
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "eu",
        "markets": "h2h"
    }

    try:
        return requests.get(url, params=params, timeout=10).json()
    except:
        return []

# ================= CORE ENGINE =================
def find_opportunities():
    matches = get_matches()
    odds = get_odds()

    candidates = []

    for m in matches:
        try:
            minute = m["fixture"]["status"]["elapsed"]
            if not minute or minute < 60 or minute > 82:
                continue

            stats = m.get("statistics")
            if not stats:
                continue

            h = stats[0]
            a = stats[1]

            for o in odds:
                if m["teams"]["home"]["name"].lower() in o.get("home_team","").lower():

                    if not o.get("bookmakers"):
                        continue

                    for out in o["bookmakers"][0]["markets"][0]["outcomes"]:
                        quota = out["price"]
                        team = out["name"]

                        features = extract(h, a, minute, quota)
                        if not features:
                            continue

                        prob_ai = predict(features)

                        prob_m = momentum_model(h, a)
                        prob_v = value_model(quota)

                        final_prob = ensemble(prob_m, prob_v, prob_ai)
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
                                "match": f"{m['teams']['home']['name']} vs {m['teams']['away']['name']}"
                            })

        except:
            continue

    return sorted(candidates, key=lambda x: x["value"], reverse=True)[:MAX_POSITIONS]

# ================= EXECUTION =================
def run():
    send("🏦 QUANT HEDGE FUND SYSTEM ONLINE")

    while True:
        try:
            if risk_check() == "STOP":
                send("🛑 RISK KILL SWITCH ATTIVO")
                time.sleep(3600)
                continue

            bets = find_opportunities()

            for b in bets:
                s = stake(b["prob"], b["quota"])
                if s <= 0:
                    continue

                open_positions.append({
                    "team": b["team"],
                    "stake": s,
                    "quota": b["quota"]
                })

                send(
                    f"🏦 INSTITUTIONAL BET\n"
                    f"{b['match']}\n"
                    f"{b['team']}\n"
                    f"⏱ {b['minute']}\n"
                    f"Quota: {b['quota']}\n"
                    f"Value: {round(b['value'],2)}\n"
                    f"Stake: {round(s,2)}€"
                )

            self_learn(b["features"], 1)  # placeholder semplificato

            time.sleep(60)

        except Exception as e:
            print("ERROR:", e)
            time.sleep(30)

run()
