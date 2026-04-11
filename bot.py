import time
import requests
import joblib
import os

# ================= CONFIG (RAILWAY ENV) =================
ODDS_API_KEY = os.getenv("ODDS_API_KEY")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

BANKROLL = 50
MAX_STAKE = 0.08

# ================= TELEGRAM =================
def send(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": msg}
        )
    except:
        pass

# ================= MODELS =================
def load_model(path):
    try:
        return joblib.load(path)
    except:
        return None

win_model = load_model("win_model.pkl")
goal_model = load_model("goal_model.pkl")
risk_model = load_model("risk_model.pkl")

# ================= API =================
def get_matches():
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
    headers = {
        "X-RapidAPI-Key": FOOTBALL_API_KEY,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }

    try:
        r = requests.get(url, headers=headers, params={"live": "all"}, timeout=10)
        return r.json().get("response", [])
    except:
        return []


def get_odds():
    try:
        r = requests.get(
            "https://api.the-odds-api.com/v4/sports/soccer/odds",
            params={
                "apiKey": ODDS_API_KEY,
                "regions": "eu",
                "markets": "h2h"
            },
            timeout=10
        )
        return r.json()
    except:
        return []

# ================= FEATURES =================
def extract(stat, key):
    try:
        for s in stat["statistics"]:
            if key in s["type"].lower():
                return float(s["value"] or 0)
    except:
        pass
    return 0


def build_features(h, a, minute, quota):
    shots = extract(h,"shots on goal") - extract(a,"shots on goal")
    danger = extract(h,"dangerous attacks") - extract(a,"dangerous attacks")
    poss = extract(h,"possession") - extract(a,"possession")
    goals = extract(h,"goals") - extract(a,"goals")
    reds = extract(h,"red cards") - extract(a,"red cards")

    dominance = shots*2 + danger*1.5 + poss*0.5

    return [shots, danger, poss, goals, reds, dominance, minute, quota], dominance

# ================= STAKE =================
def stake(prob, quota, risk):
    edge = prob - (1/quota)

    if edge < 0.05:
        return 0

    base = BANKROLL * 0.02

    if risk > 0.6:
        base *= 0.4
    elif risk < 0.3:
        base *= 1.6

    return min(base, BANKROLL * MAX_STAKE)

# ================= DECISION ENGINE =================
def decide(win_p, goal_p, risk_p, edge, dominance, minute):

    if risk_p > 0.65:
        return None

    if dominance < 18:
        return None

    if minute < 60 or minute > 83:
        return None

    if goal_p > 0.72:
        return "GOAL"

    if win_p > 0.67 and edge > 0.06:
        return "WIN"

    return None

# ================= MAIN LOOP =================
def run():

    send("🚀 BET-BOT ONLINE (RAILWAY DEPLOYED)")

    while True:

        try:
            matches = get_matches()
            odds = get_odds()

            for m in matches:

                minute = m["fixture"]["status"]["elapsed"]
                if not minute:
                    continue

                stats = m.get("statistics")
                if not stats:
                    continue

                h, a = stats

                for o in odds:

                    if m["teams"]["home"]["name"].lower() not in o.get("home_team","").lower():
                        continue

                    try:
                        outcomes = o["bookmakers"][0]["markets"][0]["outcomes"]
                    except:
                        continue

                    for out in outcomes:

                        quota = out["price"]

                        f, dominance = build_features(h,a,minute,quota)

                        win_p = win_model.predict_proba([f])[0][1] if win_model else 0.5
                        goal_p = goal_model.predict_proba([f])[0][1] if goal_model else 0.5
                        risk_p = risk_model.predict_proba([f])[0][1] if risk_model else 0.3

                        edge = win_p - (1/quota)

                        decision = decide(
                            win_p,
                            goal_p,
                            risk_p,
                            edge,
                            dominance,
                            minute
                        )

                        if decision:

                            st = stake(win_p, quota, risk_p)

                            if st <= 0:
                                continue

                            msg = f"""
🚀 {decision} SIGNAL

{m['teams']['home']['name']} vs {m['teams']['away']['name']}

📊 WIN: {round(win_p,2)}
🔥 GOAL: {round(goal_p,2)}
⚠️ RISK: {round(risk_p,2)}
📈 EDGE: {round(edge,2)}

💰 STAKE: {round(st,2)}€
🏦 BANKROLL: {BANKROLL}
"""

                            send(msg)

            time.sleep(60)

        except Exception as e:
            print("ERROR:", e)
            time.sleep(10)


if __name__ == "__main__":
    run()
