import requests, time, datetime, csv, os, pytz, sys
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

sys.stdout.reconfigure(line_buffering=True)

# ===== CONFIG =====
ODDS_API_KEY = "f0eaec5e8d2b7e2c0598b311b9e9aa32"
TOKEN = "8649464893:AAHr0VkMebISJSqa-TKV0XIZxbZPjJ7LzyU"
CHAT_ID = "545852688"
TZ = pytz.timezone('Europe/Rome')
OFFSET = 0

# Configurazione Sessione per forzare la rete di Railway
session = requests.Session()
retry = Retry(connect=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)

print("--- [LOG] Inizializzazione Sessione Elite ---")

def invia_telegram(metodo, params=None):
    url = f"https://telegram.org{TOKEN}/{metodo}"
    try:
        # User-Agent per simulare un browser ed evitare blocchi rete
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = session.get(url, params=params, headers=headers, timeout=20)
        return r.json()
    except Exception as e:
        print(f"--- [ERRORE RETE] {e} ---")
        return None

def analizza():
    url_o = "https://the-odds-api.com"
    p = {"apiKey": ODDS_API_KEY, "regions": "eu", "markets": "h2h"}
    try:
        r = session.get(url_o, params=p, timeout=20)
        res = r.json()
        for partita in res:
            try:
                bm = partita.get("bookmakers", [])
                if not bm: continue
                # Estrazione sicura quote
                outcomes = sorted(bm[0]["markets"][0]["outcomes"], key=lambda x: x['price'])
                fav = outcomes[0]
                if 1.25 <= fav["price"] <= 1.45:
                    return {"match": f"{partita['home_team']} vs {partita['away_team']}", "team": fav["name"], "quota": fav["price"]}
            except: continue
    except: pass
    return None

def run():
    global OFFSET
    print("--- [SISTEMA] BOT OPERATIVO ---")
    invia_telegram("sendMessage", {"chat_id": CHAT_ID, "text": "🚀 *SISTEMA ONLINE - RETE SBLOCCATA*", "parse_mode": "Markdown"})

    while True:
        try:
            # A. Controllo Comandi
            updates = invia_telegram("getUpdates", {"offset": OFFSET, "timeout": 10})
            if updates and updates.get("ok"):
                for u in updates["result"]:
                    OFFSET = u["update_id"] + 1
                    if "message" in u and "text" in u["message"]:
                        if "/status" in u["message"].lower():
                            invia_telegram("sendMessage", {"chat_id": CHAT_ID, "text": "📊 *STATUS*: Operativo ✅"})

            # B. Ricerca Bet
            bet = analizza()
            if bet:
                msg = f"🔥 *NUOVO SEGNALE*\n🏟 {bet['match']}\n👉 {bet['team']}\n📈 Quota: {bet['quota']}"
                invia_telegram("sendMessage", {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
                time.sleep(600)

            time.sleep(120)
        except Exception as e:
            print(f"--- [LOOP ERRORE] {e} ---")
            time.sleep(30)

if __name__ == "__main__":
    run()
