import requests
import time
import datetime
import csv
import os
import pytz

# ===== CONFIG (INSERISCI I TUOI DATI) =====
ODDS_API_KEY = "f0eaec5e8d2b7e2c0598b311b9e9aa32"
FOOTBALL_API_KEY = "50c72696adfffd60c9540455af3b7f9a"
TOKEN = "8649464893:AAHr0VkMebISJSqa-TKV0XIZxbZPjJ7LzyU"
CHAT_ID = "545852688"

FILE = "tracking.csv"
LAST_UPDATE_ID = None
MAX_BET_GIORNO = 2
TZ = pytz.timezone('Europe/Rome') # Forza orario italiano su Railway

# ===== INIT FILE =====
if not os.path.exists(FILE):
    with open(FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["data", "match", "quota", "stake", "esito", "profitto", "fixture_id"])

# ===== FUNZIONI CORE =====

def send(msg):
    try:
        url = f"https://telegram.org{TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
    except: pass

def get_bankroll():
    profit = 0
    try:
        with open(FILE, "r") as f:
            reader = csv.DictReader(f)
            for row in reader: profit += float(row["profitto"])
    except: pass
    return round(50.0 + profit, 2)

def get_stats_oggi():
    oggi = datetime.datetime.now(TZ).date()
    w, l, p = 0, 0, 0.0
    try:
        with open(FILE, "r") as f:
            for row in csv.DictReader(f):
                dt = datetime.datetime.strptime(row["data"], "%Y-%m-%d %H:%M:%S").date()
                if dt == oggi:
                    p += float(row["profitto"])
                    if row["esito"] == "WIN": w += 1
                    elif row["esito"] == "LOSS": l += 1
    except: pass
    return w, l, round(p, 2)

# ===== ANALISI ELITE (ORARIO 10:00 - 00:00) =====

def analizza():
    # Controllo Orario con Timezone Italiana
    ora_attuale = datetime.datetime.now(TZ).hour
    if ora_attuale < 10: return None # Lavora dalle 10:00 alle 23:59

    win_o, loss_o, _ = get_stats_oggi()
    if (win_o + loss_o) >= MAX_BET_GIORNO: return None

    # Chiamata API Football per match Live/Oggi
    headers = {"X-RapidAPI-Key": FOOTBALL_API_KEY, "X-RapidAPI-Host": "://rapidapi.com"}
    url_f = "https://://rapidapi.com/v3/fixtures"
    params_f = {"date": datetime.datetime.now(TZ).strftime("%Y-%m-%d")}
    
    try:
        res_f = requests.get(url_f, headers=headers, params=params_f).json().get("response", [])
        url_o = f"https://the-odds-api.com{ODDS_API_KEY}&regions=eu&markets=h2h"
        res_o = requests.get(url_o).json()
        
        for m in res_f:
            if m["fixture"]["status"]["short"] not in ["NS", "1H"]: continue
            home = m["teams"]["home"]["name"]
            
            for o in res_o:
                if home.lower() in o["home_team"].lower():
                    # Filtro quote Elite
                    outcomes = sorted(o["bookmakers"][0]["markets"][0]["outcomes"], key=lambda x: x['price'])
                    fav, quota = outcomes[0]["name"], outcomes[0]["price"]
                    opp_quota = outcomes[1]["price"]
                    
                    if 1.25 <= quota <= 1.45 and opp_quota >= 3.5:
                        return {"match": f"{o['home_team']} vs {o['away_team']}", "team": fav, "quota": quota, "id": m["fixture"]["id"]}
    except: return None
    return None

# ===== AUTO-SETTLEMENT =====

def controlla_risultati():
    headers = {"X-RapidAPI-Key": FOOTBALL_API_KEY, "X-RapidAPI-Host": "://rapidapi.com"}
    righe, aggiornato = [], False
    
    if not os.path.exists(FILE): return
    with open(FILE, "r") as f: reader = list(csv.DictReader(f))
    
    for row in reader:
        if row["esito"] == "PENDING":
            try:
                url = f"https://://rapidapi.com/v3/fixtures?id={row['fixture_id']}"
                f_data = requests.get(url, headers=headers).json()["response"][0]
                if f_data["fixture"]["status"]["short"] == "FT":
                    # Check vittoria semplificato (Home vince)
                    win = f_data["goals"]["home"] > f_data["goals"]["away"]
                    row["esito"] = "WIN" if win else "LOSS"
                    row["profitto"] = round(float(row["stake"]) * (float(row["quota"]) - 1), 2) if win else -float(row["stake"])
                    aggiornato = True
                    send(f"✅ *ESITO REGISTRATO*\n{row['match']}\nRisultato: {row['esito']}\nProfitto: {row['profitto']}€")
            except: pass
        righe.append(row)

    if aggiornato:
        with open(FILE, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["data", "match", "quota", "stake", "esito", "profitto", "fixture_id"])
            writer.writeheader(); writer.writerows(righe)

# ===== LOOP PRINCIPALE =====

def run():
    global LAST_UPDATE_ID
    send("🚀 *SISTEMA ELITE ATTIVO*\nOperativo fino alle 00:00\nTarget: 150€/gg")
    
    while True:
        try:
            # Controllo comandi Telegram (/status)
            url_tg = f"https://telegram.org{TOKEN}/getUpdates"
            res_tg = requests.get(url_tg, params={"offset": LAST_UPDATE_ID}).json()
            for u in res_tg.get("result", []):
                LAST_UPDATE_ID = u["update_id"] + 1
                if "/status" in u.get("message", {}).get("text", "").lower():
                    w, l, p = get_stats_oggi()
                    send(f"📊 *STATUS*\n💰 Bankroll: {get_bankroll()}€\n📅 Oggi: {p}€\n✅ W: {w} | ❌ L: {l}")

            controlla_risultati()
            
            # Cerca nuove Bet
            bet = analizza()
            if bet:
                stk = round(get_bankroll() * 0.05, 2)
                with open(FILE, "a", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([datetime.datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S"), bet["match"], bet["quota"], stk, "PENDING", 0, bet["id"]])
                send(f"🔥 *NUOVA BET*\n🏟 {bet['match']}\n👉 Punta: {bet['team']}\n📈 Quota: {bet['quota']}\n💰 Stake: {stk}€")
            
            time.sleep(300) # Controllo ogni 5 minuti
        except: time.sleep(60)

if __name__ == "__main__":
    run()
