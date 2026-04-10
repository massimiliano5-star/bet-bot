import requests, time, datetime, csv, os, pytz, sys

sys.stdout.reconfigure(line_buffering=True)

# ===== CONFIG =====
ODDS_API_KEY = "f0eaec5e8d2b7e2c0598b311b9e9aa32"
FOOTBALL_API_KEY = "50c72696adfffd60c9540455af3b7f94"
TOKEN = "8649464893:AAHr0VkMebISJSqa-TKV0XIZxbZPjJ7LzyU"
CHAT_ID = "545852688"
TZ = pytz.timezone('Europe/Rome')
OFFSET = 0

print("--- [SISTEMA] BOT ELITE IN ASCOLTO... ---")

def invia_tg(metodo, params=None):
    url = f"https://telegram.org{TOKEN}/{metodo}"
    try:
        r = requests.get(url, params=params, timeout=20)
        return r.json()
    except: return None

def analizza_elite():
    """Analisi scommesse attiva fino alle 23:59"""
    ora = datetime.datetime.now(TZ).hour
    if ora < 10: return None # Riposo notturno per le bet

    url_o = "https://the-odds-api.com"
    p = {"apiKey": ODDS_API_KEY, "regions": "eu", "markets": "h2h"}
    try:
        res = requests.get(url_o, params=p, timeout=15).json()
        for match in res:
            try:
                bm = match.get("bookmakers", [])
                if not bm: continue
                # Filtro Elite 1.25 - 1.45
                outcomes = sorted(bm["markets"]["outcomes"], key=lambda x: x['price'])
                fav = outcomes
                if 1.25 <= fav["price"] <= 1.45:
                    return {"match": f"{match['home_team']} vs {match['away_team']}", "team": fav["name"], "quota": fav["price"]}
            except: continue
    except: pass
    return None

def run():
    global OFFSET
    # Messaggio di conferma avvio immediato
    invia_tg("sendMessage", {"chat_id": CHAT_ID, "text": "✅ *BOT RICONNESSO E OPERATIVO*\nScrivi `/status` ora per testare.", "parse_mode": "Markdown"})

    while True:
        try:
            # 1. GESTIONE COMANDI (Sempre attiva 24/7)
            updates = invia_tg("getUpdates", {"offset": OFFSET, "timeout": 10})
            if updates and updates.get("ok"):
                for u in updates["result"]:
                    OFFSET = u["update_id"] + 1
                    if "message" in u and "text" in u["message"]:
                        testo = u["message"].lower()
                        print(f"--- [LOG] Ricevuto: {testo} ---")
                        
                        if "/status" in testo:
                            invia_tg("sendMessage", {"chat_id": CHAT_ID, "text": "📊 *STATUS ELITE*\n💰 Bankroll: 50.00€\n✅ Sistema: Online\n⚽️ Analisi: In corso..."})
                        elif "/start" in testo:
                            invia_tg("sendMessage", {"chat_id": CHAT_ID, "text": "👋 Benvenuto nel Sistema Elite! Sono pronto."})

            # 2. RICERCA BET
            bet = analizza_elite()
            if bet:
                msg = f"🔥 *NUOVO SEGNALE*\n🏟 {bet['match']}\n👉 {bet['team']}\n📈 Quota: {bet['quota']}"
                invia_tg("sendMessage", {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
                time.sleep(600) # Evita spam

            time.sleep(30) # Ciclo più veloce per rispondere ai comandi
        except Exception as e:
            print(f"--- [ERRORE] {e} ---")
            time.sleep(10)

if __name__ == "__main__":
    run()
