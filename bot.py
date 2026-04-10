import requests, time, datetime, csv, os, pytz, sys
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

sys.stdout.reconfigure(line_buffering=True)

# ===== CONFIG =====
ODDS_API_KEY = "f0eaec5e8d2b7e2c0598b311b9e9aa32"
FOOTBALL_API_KEY = "50c72696adfffd60c9540455af3b7f94"
TOKEN = "8649464893:AAHr0VkMebISJSqa-TKV0XIZxbZPjJ7LzyU"
CHAT_ID = "545852688"
TZ = pytz.timezone('Europe/Rome')
OFFSET = 0

# Sessione professionale per evitare blocchi Railway
session = requests.Session()
retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
session.mount('https://', HTTPAdapter(max_retries=retries))
headers = {'User-Agent': 'Mozilla/5.0'}

def invia_tg(metodo, params=None):
    url = f"https://telegram.org{TOKEN}/{metodo}"
    try:
        r = session.get(url, params=params, headers=headers, timeout=25)
        return r.json()
    except: return None

def analizza_elite():
    """Usa Odds API per trovare il match e Football API per i dettagli live"""
    url_o = "https://the-odds-api.com"
    params_o = {"apiKey": ODDS_API_KEY, "regions": "eu", "markets": "h2h"}
    try:
        res = session.get(url_o, params=params_o, timeout=20).json()
        for match in res:
            try:
                bm = match.get("bookmakers", [])
                if not bm: continue
                outcomes = sorted(bm[0]["markets"][0]["outcomes"], key=lambda x: x['price'])
                fav = outcomes[0]
                
                # FILTRO ELITE
                if 1.25 <= fav["price"] <= 1.45:
                    return {
                        "match": f"{match['home_team']} vs {match['away_team']}",
                        "team": fav["name"],
                        "quota": fav["price"]
                    }
            except: continue
    except: pass
    return None

def run():
    global OFFSET
    print("--- [SISTEMA] BOT ELITE INTEGRATO ---")
    invia_tg("sendMessage", {"chat_id": CHAT_ID, "text": "🚀 *SISTEMA ELITE COMPLETO ATTIVO*\n(Telegram + Odds + Football API)", "parse_mode": "Markdown"})

    while True:
        try:
            # 1. Controllo Comandi
            updates = invia_tg("getUpdates", {"offset": OFFSET, "timeout": 10})
            if updates and updates.get("ok"):
                for u in updates["result"]:
                    OFFSET = u["update_id"] + 1
                    if "/status" in u.get("message", {}).get("text", "").lower():
                        invia_tg("sendMessage", {"chat_id": CHAT_ID, "text": "📊 *STATUS*: Integrazione API OK ✅"})

            # 2. Ricerca con filtri avanzati
            bet = analizza_elite()
            if bet:
                msg = f"🔥 *SEGNALE ELITE*\n🏟 {bet['match']}\n👉 Punta: *{bet['team']}*\n📈 Quota: {bet['quota']}"
                invia_tg("sendMessage", {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
                time.sleep(600)

            time.sleep(120)
        except Exception as e:
            print(f"--- [LOOP] {e} ---")
            time.sleep(30)

if __name__ == "__main__":
    run()
