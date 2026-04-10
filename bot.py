import requests, time, datetime, csv, os, pytz, sys

sys.stdout.reconfigure(line_buffering=True)

# ===== CONFIG =====
ODDS_API_KEY = "f0eaec5e8d2b7e2c0598b311b9e9aa32"
TOKEN = "8649464893:AAHr0VkMebISJSqa-TKV0XIZxbZPjJ7LzyU"
CHAT_ID = "545852688"
FILE_CSV = "tracking.csv"
TZ = pytz.timezone('Europe/Rome')
OFFSET = 0

print("--- [LOG] Inizializzazione ---")

if not os.path.exists(FILE_CSV):
    with open(FILE_CSV, "w", newline="") as f:
        csv.writer(f).writerow(["data", "match", "quota", "stake", "esito", "profitto", "fixture_id"])

def invia_telegram(metodo, params=None):
    """Gestione sicura delle chiamate Telegram per evitare errori di parsing"""
    url = f"https://telegram.org{TOKEN}/{metodo}"
    try:
        r = requests.get(url, params=params, timeout=15)
        return r.json()
    except Exception as e:
        print(f"--- [ERRORE RETE] {e} ---")
        return None

def analizza():
    """Ricerca match ELITE"""
    url_o = "https://the-odds-api.com"
    p = {"apiKey": ODDS_API_KEY, "regions": "eu", "markets": "h2h"}
    try:
        res = requests.get(url_o, params=p, timeout=15).json()
        for partita in res:
            try:
                outcomes = sorted(partita["bookmakers"][0]["markets"][0]["outcomes"], key=lambda x: x['price'])
                fav = outcomes[0]
                if 1.25 <= fav["price"] <= 1.45:
                    return {"match": f"{partita['home_team']} vs {partita['away_team']}", "team": fav["name"], "quota": fav["price"]}
            except: continue
    except: pass
    return None

def run():
    global OFFSET
    print("--- [SISTEMA] BOT OPERATIVO ---")
    invia_telegram("sendMessage", {"chat_id": CHAT_ID, "text": "🚀 *SISTEMA ONLINE*", "parse_mode": "Markdown"})

    while True:
        try:
            # A. Controllo Comandi
            updates = invia_telegram("getUpdates", {"offset": OFFSET, "timeout": 10})
            if updates and updates.get("ok"):
                for u in updates["result"]:
                    OFFSET = u["update_id"] + 1
                    if "/status" in u.get("message", {}).get("text", "").lower():
                        invia_telegram("sendMessage", {"chat_id": CHAT_ID, "text": "📊 *STATUS*: Operativo ✅"})

            # B. Ricerca Bet
            bet = analizza()
            if bet:
                msg = f"🔥 *NUOVO SEGNALE*\n🏟 {bet['match']}\n👉 {bet['team']}\n📈 Quota: {bet['quota']}"
                invia_telegram("sendMessage", {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
                time.sleep(600) # Evita spam se trova un match

            time.sleep(120)
        except Exception as e:
            print(f"--- [LOOP] {e} ---")
            time.sleep(30)

if __name__ == "__main__":
    run()
