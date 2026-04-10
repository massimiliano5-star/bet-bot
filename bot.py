import requests
import time
import datetime
import csv
import os
import pytz
import sys

# Forza l'output immediato nei log di Railway per il debug
sys.stdout.reconfigure(line_buffering=True)

# ===== CONFIGURAZIONE (Verifica che i dati siano corretti) =====
ODDS_API_KEY = "f0eaec5e8d2b7e2c0598b311b9e9aa32"
FOOTBALL_API_KEY = "50c72696adfffd60c9540455af3b7f94"
TOKEN = "8649464893:AAHr0VkMebISJSqa-TKV0XIZxbZPjJ7LzyU"
CHAT_ID = "545852688"

FILE = "tracking.csv"
TZ = pytz.timezone('Europe/Rome')
MAX_BET_GIORNO = 2
LAST_UPDATE_ID = 0

print("--- [SISTEMA] Inizializzazione bot... ---")

# ===== INIZIALIZZAZIONE FILE CSV =====
if not os.path.exists(FILE):
    with open(FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["data", "match", "quota", "stake", "esito", "profitto", "fixture_id"])

# ===== FUNZIONE INVIO MESSAGGI =====
def send(msg):
    url = f"https://telegram.org{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, json=payload, timeout=15)
        if r.status_code == 200:
            print(f"--- [TELEGRAM] Messaggio inviato: {msg[:20]}... ---")
        else:
            print(f"--- [ERRORE] Telegram ha risposto con codice {r.status_code}: {r.text} ---")
    except Exception as e:
        print(f"--- [ERRORE] Impossibile connettersi a Telegram: {e} ---")

# ===== STATISTICHE =====
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
    except Exception as e:
        print(f"--- [ERRORE] Lettura statistiche: {e} ---")
    return w, l, round(p, 2)

# ===== ANALISI ELITE (ORARIO 10:00 - 00:00) =====
def analizza():
    ora_attuale = datetime.datetime.now(TZ).hour
    if ora_attuale < 10: return None # Il bot riposa di notte

    w_oggi, l_oggi, _ = get_stats_oggi()
    if (w_oggi + l_oggi) >= MAX_BET_GIORNO:
        return None

    print("--- [ANALISI] Ricerca quote in corso... ---")
    try:
        url_o = f"https://the-odds-api.com{ODDS_API_KEY}&regions=eu&markets=h2h"
        r = requests.get(url_o, timeout=15)
        if r.status_code != 200:
            print(f"--- [ERRORE] Odds API: {r.status_code} ---")
            return None
        
        odds_data = r.json()
        for o in odds_data:
            try:
                # Navigazione corretta nella struttura di Odds API
                bookmakers = o.get("bookmakers", [])
                if not bookmakers: continue
                
                outcomes = bookmakers[0]["markets"][0]["outcomes"]
                # Ordina per trovare la favorita (quota minima)
                outcomes_sorted = sorted(outcomes, key=lambda x: x['price'])
                fav = outcomes_sorted[0]
                
                # FILTRO ELITE (Quota 1.25 - 1.45)
                if 1.25 <= fav["price"] <= 1.45:
                    return {
                        "match": f"{o['home_team']} vs {o['away_team']}",
                        "team": fav["name"],
                        "quota": fav["price"],
                        "id": "LIVE" # Placeholder per test
                    }
            except: continue
    except Exception as e:
        print(f"--- [ERRORE] Analisi: {e} ---")
    return None

# ===== LOOP PRINCIPALE =====
def run():
    global LAST_UPDATE_ID
    print("--- [SISTEMA] Bot Online e Operativo! ---")
    send("🚀 *SISTEMA ELITE ONLINE*\nMonitoraggio attivo fino alle 00:00.\nInvia `/status` per il report.")
    
    while True:
        try:
            # 1. Gestione Comandi Telegram
            url_tg = f"https://telegram.org{TOKEN}/getUpdates"
            params = {"offset": LAST_UPDATE_ID, "timeout": 10}
            res_tg = requests.get(url_tg, params=params, timeout=20).json()
            
            if res_tg.get("ok"):
                for u in res_tg.get("result", []):
                    LAST_UPDATE_ID = u["update_id"] + 1
                    if "message" in u and "text" in u["message"]:
                        txt = u["message"].lower()
                        if "/status" in txt:
                            w, l, p = get_stats_oggi()
                            send(f"📊 *STATUS ATTUALE*\n💰 Profitto Oggi: {p}€\n✅ Vinte: {w}\n❌ Perse: {l}")

            # 2. Ricerca Nuove Opportunità
            bet = analizza()
            if bet:
                stk = 5.0 # Stake di test fisso
                data_ora = datetime.datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S")
                with open(FILE, "a", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([data_ora, bet["match"], bet["quota"], stk, "PENDING", 0, bet["id"]])
                
                send(f"🔥 *NUOVA BET RILEVATA*\n🏟 Match: {bet['match']}\n👉 Punta: *{bet['team']}*\n📈 Quota: {bet['quota']}\n💰 Stake: {stk}€")
            
            # Attesa tra i cicli (60 secondi)
            time.sleep(60)
            
        except Exception as e:
            print(f"--- [CRASH] Errore nel loop: {e} ---")
            time.sleep(15)

if __name__ == "__main__":
    run()
