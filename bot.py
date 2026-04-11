import time
import requests
import os

# ================= CONFIG (RAILWAY ENV) =================
# Cambia il nome su Railway: da FOOTBALL_API_KEY a API_FOOTBALL_KEY (per chiarezza)
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY") 
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

BANKROLL = 50
SENT_SIGNALS = {} 

# ================= TELEGRAM =================
def send(msg):
    url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg}, timeout=10)
        print(f"📡 Telegram Response: {r.status_code}")
    except Exception as e:
        print(f"❌ Errore Telegram: {e}")

# ================= API FOOTBALL (DIRETTO - NO RAPIDAPI) =================
def get_matches():
    # URL DIRETTO di API-Football
    url = "https://api-sports.io"
    
    # HEADER CORRETTO per API-Football
    headers = {
        "x-apisports-key": API_FOOTBALL_KEY
    }
    
    try:
        r = requests.get(url, headers=headers, params={"live": "all"}, timeout=10)
        data = r.json()
        
        # Log di debug per vedere se la chiave funziona
        if "errors" in data and data["errors"]:
            print(f"❌ Errore API-Football: {data['errors']}")
            return []
            
        return data.get("response", [])
    except Exception as e:
        print(f"❌ Errore connessione API: {e}")
        return []

# ================= ANALISI E LOOP =================
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

    return (h_shots - a_shots) * 3 + (h_danger - a_danger) * 1.2 + (h_poss - 50) * 0.5

def run():
    print("--- 🚀 AVVIO BOT (API-SPORTS DIRETTO) ---")
    send("🚀 BOT ONLINE\nAPI: Diretta (v3)\nRange: 45'-80'")
    
    while True:
        try:
            matches = get_matches()
            print(f"🔎 Partite analizzate: {len(matches)}")

            for m in matches:
                m_id = m["fixture"]["id"]
                if m_id in SENT_SIGNALS: continue

                minute = m["fixture"]["status"]["elapsed"]
                if not minute or minute < 45 or minute > 80: continue

                stats = m.get("statistics")
                if not stats or len(stats) < 2: continue

                h_stat, a_stat = stats
                dom_score = analyze_pressure(h_stat, a_stat)

                # Soglia abbassata a 10 per il test live
                if dom_score > 10:
                    msg = f"⚽ SIGNAL: CASA DOMINA ({round(dom_score)})\n🏆 {m['teams']['home']['name']} vs {m['teams']['away']['name']}\n⏰ Min: {minute}'"
                    send(msg)
                    SENT_SIGNALS[m_id] = True

            time.sleep(60)
        except Exception as e:
            print(f"❌ Errore: {e}")
            time.sleep(20)

if __name__ == "__main__":
    run()
