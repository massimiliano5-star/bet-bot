import time
import requests
import os

# ================= CONFIG (RAILWAY ENV) =================
# Assicurati che i nomi delle variabili su Railway siano IDENTICI a questi
ODDS_API_KEY = os.getenv("ODDS_API_KEY")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

BANKROLL = 50
SENT_SIGNALS = {} 

# ================= TELEGRAM (CON DEBUG) =================
def send(msg):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ ERRORE: Variabili Telegram mancanti nelle impostazioni Railway!")
        return

    url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg}
    
    try:
        r = requests.post(url, json=payload, timeout=10)
        print(f"📡 Invio Telegram: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"❌ Errore di rete Telegram: {e}")

# ================= LOGICA DI ANALISI =================
def analyze_pressure(h, a):
    def get_val(stat, key):
        for s in stat.get("statistics", []):
            if key in s["type"].lower():
                val = s["value"]
                if isinstance(val, str) and "%" in val:
                    return float(val.replace("%", ""))
                return float(val or 0)
        return 0

    h_shots = get_val(h, "shots on goal")
    a_shots = get_val(a, "shots on goal")
    h_danger = get_val(h, "dangerous attacks")
    a_danger = get_val(a, "dangerous attacks")
    h_poss = get_val(h, "possession")

    # Formula semplificata per il test
    dominance_score = (h_shots - a_shots) * 3 + (h_danger - a_danger) * 1.2 + (h_poss - 50) * 0.5
    return dominance_score

# ================= API CALLS =================
def get_matches():
    url = "https://rapidapi.com"
    headers = {
        "X-RapidAPI-Key": FOOTBALL_API_KEY,
        "X-RapidAPI-Host": "://rapidapi.com"
    }
    try:
        r = requests.get(url, headers=headers, params={"live": "all"}, timeout=10)
        return r.json().get("response", [])
    except Exception as e:
        print(f"❌ Errore API Football: {e}")
        return []

# ================= MAIN LOOP =================
def run():
    print("--- 🚀 AVVIO BOT IN CORSO ---")
    send("🚀 BET-BOT ONLINE\nRange: 45'-80'\nStato: Monitoraggio attivo")
    
    while True:
        try:
            matches = get_matches()
            print(f"🔎 Analizzando {len(matches)} partite live...")

            for m in matches:
                m_id = m["fixture"]["id"]
                home_n = m["teams"]["home"]["name"]
                away_n = m["teams"]["away"]["name"]

                if m_id in SENT_SIGNALS:
                    continue

                minute = m["fixture"]["status"]["elapsed"]
                
                # RANGE RICHIESTO: 45-80
                if not minute or minute < 45 or minute > 80:
                    continue

                stats = m.get("statistics")
                if not stats or len(stats) < 2:
                    continue

                h_stat, a_stat = stats
                dom_score = analyze_pressure(h_stat, a_stat)

                # SOGLIA DI TEST (abbassata a 15 per vedere se arrivano segnali)
                decision = None
                if dom_score > 15:
                    decision = f"🔥 DOMINIO CASA ({round(dom_score)})"
                elif dom_score < -15:
                    decision = f"🔥 DOMINIO OSPITE ({round(abs(dom_score))})"

                if decision:
                    msg = (f"⚽ SIGNAL: {decision}\n\n"
                           f"🏆 {home_n} vs {away_n}\n"
                           f"⏰ Minuto: {minute}'\n"
                           f"📊 Pressione: {round(dom_score, 1)}")
                    
                    send(msg)
                    SENT_SIGNALS[m_id] = True
                    print(f"✅ Segnale inviato per {home_n}")

            time.sleep(60)

        except Exception as e:
            print(f"❌ Errore nel ciclo principale: {e}")
            time.sleep(20)

if __name__ == "__main__":
    run()
