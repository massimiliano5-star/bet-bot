import requests
import time
import datetime
import csv
import os
import pytz
import sys

# Forza l'output immediato nei log di Railway
sys.stdout.reconfigure(line_buffering=True)

# ===== CONFIG =====
ODDS_API_KEY = "f0eaec5e8d2b7e2c0598b311b9e9aa32"
FOOTBALL_API_KEY = "50c72696adfffd60c9540455af3b7f94"
TOKEN = "8649464893:AAHr0VkMebISJSqa-TKV0XIZxbZPjJ7LzyU"
CHAT_ID = "545852688"

FILE = "tracking.csv"
TZ = pytz.timezone('Europe/Rome')
MAX_BET_GIORNO = 2
LAST_UPDATE_ID = 0

print("--- [SISTEMA] Avvio in corso... ---")

# ===== INIT FILE =====
if not os.path.exists(FILE):
    with open(FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["data", "match", "quota", "stake", "esito", "profitto", "fixture_id"])

def send(msg):
    try:
        url = f"https://telegram.org{TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except Exception as e:
        print(f"Errore invio Telegram: {e}")

def get_stats_oggi():
    oggi = datetime.datetime.now(TZ).date()
    w, l, p = 0, 0, 0.0
    try:
        if os.path.exists(FILE):
            with open(FILE, "r") as f:
                for row in csv.DictReader(f):
                    dt = datetime.datetime.strptime(row["data"], "%Y-%m-%d %H:%M:%S").date()
                    if dt == oggi:
                        p += float(row["profitto"])
                        if row["esito"] == "WIN": w += 1
                        elif row["esito"] == "LOSS": l += 1
    except Exception as e: print(f"Errore stats: {e}")
    return w, l, round(p, 2)

# ===== ANALISI ELITE =====
def analizza():
    ora = datetime.datetime.now(TZ).hour
    if ora < 10: return None

    w, l, _ = get_stats_oggi()
    if (w + l) >= MAX_BET_GIORNO: return None

    print("--- [ANALISI] Ricerca match in corso... ---")
    try:
        # Odds API
        url_o = f"https://the-odds-api.com{ODDS_API_KEY}&regions=eu&markets=h2h"
        odds_data = requests.get(url_o, timeout=10).json()
        
        for o in odds_data:
            # Estraiamo le quote correttamente
            try:
                outcomes = o["bookmakers"][0]["markets"][0]["outcomes"]
                outcomes = sorted(outcomes, key=lambda x: x['price'])
                fav = outcomes[0] # La quota più bassa
                
                # Filtro Elite
                if 1.25 <= fav["price"] <= 1.45:
                    print(f"Match trovato: {o['home_team']} quota {fav['price']}")
                    return {
                        "match": f"{o['home_team']} vs {o['away_team']}",
                        "team": fav["name"],
                        "quota": fav["price"],
                        "id": "LIVE" # Semplificato per test
                    }
            except: continue
    except Exception as e:
        print(f"Errore API: {e}")
    return None

# ===== LOOP PRINCIPALE =====
def run():
    global LAST_UPDATE_ID
    print("--- [SISTEMA] Bot Online! ---")
    send("🚀 *SISTEMA ELITE ONLINE*\nBot attivo su Railway.\nScrivi `/status` per i dati.")
    
    while True:
        try:
            # Controllo comandi Telegram
            url_tg = f"https://telegram.org{TOKEN}/getUpdates"
            res_tg = requests.get(url_tg, params={"offset": LAST_UPDATE_ID, "timeout": 1}, timeout=10).json()
            
            for u in res_tg.get("result", []):
                LAST_UPDATE_ID = u["update_id"] + 1
                if "message" in u and "text" in u["message"]:
                    txt = u["message"].lower()
                    if "/status" in txt:
                        w, l, p = get_stats_oggi()
                        send(f"📊 *STATUS*\n💰 Profitto Oggi: {p}€\n✅ W: {w} | ❌ L: {l}")

            # Analisi Bet
            bet = analizza()
            if bet:
                stk = 5.0 # Stake fisso per test
                data_ora = datetime.datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S")
                with open(FILE, "a", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([data_ora, bet["match"], bet["quota"], stk, "PENDING", 0, bet["id"]])
                
                send(f"🔥 *NUOVA BET*\n🏟 {bet['match']}\n👉 Punta: {bet['team']}\n📈 Quota: {bet['quota']}\n💰 Stake: {stk}€")
            
            time.sleep(60) # Accorciato per i test iniziali
        except Exception as e:
            print(f"Errore nel loop: {e}")
            time.sleep(10)

if __name__ == "__main__":
    run()
