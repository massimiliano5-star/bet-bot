import requests
import time
import datetime
import csv
import os

# ===== CONFIG (INSERISCI I TUOI DATI) =====
ODDS_API_KEY = "f0eaec5e8d2b7e2c0598b311b9e9aa32"
FOOTBALL_API_KEY = "50c72696adfffd60c9540455af3b7f9a"
TOKEN = "8649464893:AAHr0VkMebISJSqa-TKV0XIZxbZPjJ7LzyU"
CHAT_ID = "545852688"

FILE = "tracking.csv"
LAST_UPDATE_ID = None
MAX_BET_GIORNO = 2

# ===== INIT FILE =====
if not os.path.exists(FILE):
    with open(FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["data", "match", "quota", "stake", "esito", "profitto", "fixture_id"])

# ===== FUNZIONI CORE =====

def send(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
    except: pass

def get_bankroll():
    profit = 0
    try:
        with open(FILE, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                profit += float(row["profitto"])
    except: pass
    return round(50.0 + profit, 2)

def get_stats_oggi():
    today = datetime.date.today()
    win, loss, prof = 0, 0, 0.0
    try:
        with open(FILE, "r") as f:
            for row in csv.DictReader(f):
                dt = datetime.datetime.strptime(row["data"], "%Y-%m-%d %H:%M:%S").date()
                if dt == today:
                    prof += float(row["profitto"])
                    if row["esito"] == "WIN": win += 1
                    else: loss += 1
    except: pass
    return win, loss, round(prof, 2)

# ===== API FOOTBALL & ODDS =====

def get_matches_live_and_upcoming():
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
    headers = {"X-RapidAPI-Key": FOOTBALL_API_KEY, "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"}
    params = {"date": datetime.datetime.now().strftime("%Y-%m-%d")}
    try:
        res = requests.get(url, headers=headers, params=params, timeout=10)
        return res.json().get("response", [])
    except: return []

def get_odds():
    url = "https://api.the-odds-api.com/v4/sports/soccer/odds/"
    params = {"apiKey": ODDS_API_KEY, "regions": "eu", "markets": "h2h"}
    try:
        res = requests.get(url, params=params, timeout=10)
        return res.json() if res.status_code == 200 else []
    except: return []

# ===== LOGICA ELITE =====

def analizza():
    # Controllo Orario (10:00 - 22:00)
    ora = datetime.datetime.now().hour
    if ora < 10 or ora > 22: return None

    win_oggi, loss_oggi, _ = get_stats_oggi()
    if (win_oggi + loss_oggi) >= MAX_BET_GIORNO: return None

    matches = get_matches_live_and_upcoming()
    odds = get_odds()
    if not matches or not odds: return None

    for m in matches:
        # Solo match non ancora iniziati o appena iniziati
        if m["fixture"]["status"]["short"] not in ["NS", "1H"]: continue
        
        home = m["teams"]["home"]["name"]
        fixture_id = m["fixture"]["id"]

        for o in odds:
            if home.lower() in o["home_team"].lower():
                try:
                    outcomes = o["bookmakers"][0]["markets"][0]["outcomes"]
                    # Ordina per quota più bassa
                    outcomes = sorted(outcomes, key=lambda x: x['price'])
                    fav = outcomes[0]  # Favorita
                    opp_quota = outcomes[2]['price'] if len(outcomes) > 2 else outcomes[1]['price'] # Quota avversario/pareggio

                    # FILTRO ELITE OTTIMIZZATO
                    if 1.25 <= fav["price"] <= 1.45 and opp_quota >= 3.5:
                        return {
                            "match": f"{o['home_team']} vs {o['away_team']}",
                            "team": fav["name"],
                            "quota": fav["price"],
                            "id": fixture_id
                        }
                except: continue
    return None

# ===== AUTO-SETTLEMENT =====

def controlla_risultati():
    headers = {"X-RapidAPI-Key": FOOTBALL_API_KEY, "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"}
    righe = []
    aggiornato = False
    
    if not os.path.exists(FILE): return

    with open(FILE, "r") as f:
        reader = list(csv.DictReader(f))
    
    for row in reader:
        if row["esito"] == "PENDING":
            url = f"https://rapidapi.com{row['fixture_id']}"
            res = requests.get(url, headers=headers).json()
            f_data = res["response"][0]
            
            if f_data["fixture"]["status"]["short"] == "FT":
                g_h = f_data["goals"]["home"]
                g_a = f_data["goals"]["away"]
                team_bet = row["match"].split(" vs ")[0] # Semplificato
                
                # Check vittoria
                win = False
                if g_h > g_a: win = True # Assumiamo bet su Home per semplicità filtro
                
                row["esito"] = "WIN" if win else "LOSS"
                row["profitto"] = round(float(row["stake"]) * (float(row["quota"]) - 1), 2) if win else -float(row["stake"])
                aggiornato = True
                send(f"✅ ESITO DISPONIBILE\n{row['match']}\nRisultato: {row['esito']}\nProfitto: {row['profitto']}€")
        righe.append(row)

    if aggiornato:
        with open(FILE, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["data", "match", "quota", "stake", "esito", "profitto", "fixture_id"])
            writer.writeheader()
            writer.writerows(righe)

# ===== COMANDI TELEGRAM =====

def check_commands():
    global LAST_UPDATE_ID
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    try:
        res = requests.get(url, params={"offset": LAST_UPDATE_ID}).json()
        for u in res.get("result", []):
            LAST_UPDATE_ID = u["update_id"] + 1
            txt = u.get("message", {}).get("text", "").lower()
            if "/status" in txt:
                w, l, p = get_stats_oggi()
                send(f"📊 *STATUS ELITE*\n\n💰 Bankroll: {get_bankroll()}€\n📅 Profitto Oggi: {p}€\n✅ W: {w} | ❌ L: {l}\n🚀 Target 150€: {round((p/150)*100,1)}%")
    except: pass

# ===== LOOP PRINCIPALE =====

def run():
    send("🚀 *SISTEMA ELITE AVVIATO*\nMonitoraggio attivo 10:00-22:00\nTarget: 150€/giorno")
    
    while True:
        try:
            check_commands()
            controlla_risultati()
            
            # Analisi per nuova Bet
            bet = analizza()
            if bet:
                stk = round(get_bankroll() * 0.05, 2) # Stake 5%
                with open(FILE, "a", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), bet["match"], bet["quota"], stk, "PENDING", 0, bet["id"]])
                
                send(f"🔥 *NUOVA BET ELITE*\n\n🏟 {bet['match']}\n👉 Punta su: *{bet['team']}*\n📈 Quota: {bet['quota']}\n💰 Stake: {stk}€")
            
            time.sleep(300) # Controlla ogni 5 minuti
        except Exception as e:
            print(f"Errore: {e}")
            time.sleep(60)

if __name__ == "__main__":
    run()
