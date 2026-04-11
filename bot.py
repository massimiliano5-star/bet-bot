import time
import requests
import joblib
import os
from thefuzz import fuzz # Necessaria per il matching nomi

# ================= CONFIG =================
ODDS_API_KEY = os.getenv("ODDS_API_KEY")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

BANKROLL = 50
MAX_STAKE = 0.08
SENT_SIGNALS = {} # Per evitare duplicati: {match_id: timestamp}

# ================= UTILS =================
def send(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      json={"chat_id": TELEGRAM_CHAT_ID, "text": msg}, timeout=5)
    except: pass

def load_model(path):
    return joblib.load(path) if os.path.exists(path) else None

win_model = load_model("win_model.pkl")
goal_model = load_model("goal_model.pkl")
risk_model = load_model("risk_model.pkl")

# ================= API =================
def get_matches():
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
    headers = {"X-RapidAPI-Key": FOOTBALL_API_KEY, "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"}
    try:
        r = requests.get(url, headers=headers, params={"live": "all"}, timeout=10)
        return r.json().get("response", [])
    except: return []

def get_odds():
    try:
        r = requests.get("https://api.the-odds-api.com/v4/sports/soccer/odds",
                         params={"apiKey": ODDS_API_KEY, "regions": "eu", "markets": "h2h"}, timeout=10)
        return r.json()
    except: return []

# ================= LOGIC =================
def build_features(h, a, minute, quota):
    def extract(stat, key):
        for s in stat.get("statistics", []):
            if key in s["type"].lower(): return float(s["value"] or 0)
        return 0

    shots = extract(h,"shots on goal") - extract(a,"shots on goal")
    danger = extract(h,"dangerous attacks") - extract(a,"dangerous attacks")
    poss = extract(h,"possession") - extract(a,"possession")
    reds = extract(h,"red cards") - extract(a,"red cards")
    goals = (h.get("goals") or 0) - (a.get("goals") or 0)

    dominance = shots*2 + danger*1.5 + (poss/10)
    return [shots, danger, poss, goals, reds, dominance, minute, quota], dominance

def stake_calc(prob, quota, risk):
    edge = prob - (1/quota)
    if edge < 0.05: return 0
    base = BANKROLL * 0.02
    if risk > 0.6: base *= 0.4
    elif risk < 0.3: base *= 1.6
    return min(base, BANKROLL * MAX_STAKE)

def run():
    send("🚀 BET-BOT ONLINE & OPTIMIZED")
    last_odds_check = 0
    cached_odds = []

    while True:
        try:
            # 1. Risparmia chiamate API Odds (ogni 5 min)
            if time.time() - last_odds_check > 300:
                cached_odds = get_odds()
                last_odds_check = time.time()

            matches = get_matches()

            for m in matches:
                m_id = m["fixture"]["id"]
                # 2. Evita segnali duplicati per 2 ore
                if m_id in SENT_SIGNALS and (time.time() - SENT_SIGNALS[m_id] < 7200):
                    continue

                minute = m["fixture"]["status"]["elapsed"]
                if not (60 <= (minute or 0) <= 83): continue

                stats = m.get("statistics")
                if not stats or len(stats) < 2: continue
                h_stat, a_stat = stats

                for o in cached_odds:
                    # 3. Fuzzy matching per nomi squadre (es. "Man Utd" vs "Manchester United")
                    score = fuzz.partial_ratio(m["teams"]["home"]["name"].lower(), o.get("home_team","").lower())
                    if score < 85: continue

                    try:
                        quota = o["bookmakers"][0]["markets"][0]["outcomes"][0]["price"] # Esempio su Home
                        f, dominance = build_features(h_stat, a_stat, minute, quota)

                        win_p = win_model.predict_proba([f])[0][1] if win_model else 0.5
                        goal_p = goal_model.predict_proba([f])[0][1] if goal_model else 0.5
                        risk_p = risk_model.predict_proba([f])[0][1] if risk_model else 0.3

                        edge = win_p - (1/quota)

                        if dominance > 18 and risk_p < 0.65:
                            decision = "GOAL" if goal_p > 0.72 else ("WIN" if (win_p > 0.67 and edge > 0.06) else None)
                            
                            if decision:
                                st = stake_calc(win_p, quota, risk_p)
                                if st > 0:
                                    msg = f"🚀 {decision}\n{m['teams']['home']['name']} vs {m['teams']['away']['name']}\n📊 Prob: {round(win_p,2)} | Quota: {quota}\n💰 Stake: {round(st,2)}€"
                                    send(msg)
                                    SENT_SIGNALS[m_id] = time.time()
                    except: continue

            time.sleep(60)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(20)

if __name__ == "__main__":
    run()
