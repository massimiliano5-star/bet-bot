import requests, time, datetime, csv, os, pytz, sys

sys.stdout.reconfigure(line_buffering=True)

# ===== CONFIGURAZIONE CORRETTA =====
ODDS_API_KEY="f0eaec5e8d2b7e2c0598b311b9e9aa32"
FOOTBALL_API_KEY="50c72696adfffd60c9540455af3b7f94"
TOKEN="8649464893:AAHr0VkMebISJSqa-TKV0XIZxbZPjJ7LzyU"
CHAT_ID="545852688"


FILE = "tracking.csv"
TZ = pytz.timezone('Europe/Rome')
MAX_BET_GIORNO = 2
LAST_UPDATE_ID = 0

if not os.path.exists(FILE):
    with open(FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["data", "match", "quota", "stake", "esito", "profitto", "fixture_id"])

def send(msg):
    # CORREZIONE: Assicuriamoci che l'URL sia formattato perfettamente
    base_url = "https://telegram.org" + TOKEN + "/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        r = requests.post(base_url, json=payload, timeout=15)
        print(f"--- [TELEGRAM] Status: {r.status_code} ---")
    except Exception as e:
        print(f"--- [ERRORE INVIO] {e} ---")

def get_stats_oggi():
    oggi = datetime.datetime.now(TZ).date()
    w, l, p = 0, 0, 0.0
    try:
        if os.path.exists(FILE):
            with open(FILE, "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    dt = datetime.datetime.strptime(row["data"], "%Y-%m-%d %H:%M:%S").date()
                    if dt == oggi:
                        p += float(row["profitto"])
                        if row["esito"] == "WIN": w += 1
                        elif row["esito"] == "LOSS": l += 1
    except: pass
    return w, l, round(p, 2)

def analizza():
    ora = datetime.datetime.now(TZ).hour
    if ora < 10: return None
    w_o, l_o, _ = get_stats_oggi()
    if (w_o + l_o) >= MAX_BET_GIORNO: return None

    try:
        url_o = f"https://the-odds-api.com{ODDS_API_KEY}&regions=eu&markets=h2h"
        res = requests.get(url_o, timeout=15).json()
        for o in res:
            try:
                outcomes = sorted(o["bookmakers"][0]["markets"][0]["outcomes"], key=lambda x: x['price'])
                fav = outcomes[0]
                if 1.25 <= fav["price"] <= 1.45:
                    return {"match": f"{o['home_team']} vs {o['away_team']}", "team": fav["name"], "quota": fav["price"], "id": "LIVE"}
            except: continue
    except: pass
    return None

def run():
    global LAST_UPDATE_ID
    print("--- [SISTEMA] Bot Operativo! ---")
    send("🚀 *SISTEMA ELITE ONLINE*")
    
    while True:
        try:
            # CORREZIONE: URL getUpdates formattato correttamente
            url_tg = "https://telegram.org" + TOKEN + "/getUpdates"
            res_tg = requests.get(url_tg, params={"offset": LAST_UPDATE_ID, "timeout": 10}, timeout=20).json()
            
            if res_tg.get("ok"):
                for u in res_tg.get("result", []):
                    LAST_UPDATE_ID = u["update_id"] + 1
                    if "message" in u and "text" in u["message"]:
                        if "/status" in u["message"].lower():
                            w, l, p = get_stats_oggi()
                            send(f"📊 *STATUS*\n💰 Oggi: {p}€\n✅ W: {w} | ❌ L: {l}")

            bet = analizza()
            if bet:
                stk = 5.0
                with open(FILE, "a", newline="") as f:
                    csv.writer(f).writerow([datetime.datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S"), bet["match"], bet["quota"], stk, "PENDING", 0, bet["id"]])
                send(f"🔥 *NUOVA BET*\n🏟 {bet['match']}\n👉 {bet['team']}\n📈 Quota: {bet['quota']}")
            
            time.sleep(60)
        except Exception as e:
            print(f"--- [ERRORE LOOP] {e} ---")
            time.sleep(20)

if __name__ == "__main__":
    run()
