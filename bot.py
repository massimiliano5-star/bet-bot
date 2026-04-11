import time
import requests
import os
from thefuzz import fuzz

# ================= CONFIG (RAILWAY ENV) =================
ODDS_API_KEY = os.getenv("ODDS_API_KEY")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

BANKROLL = 50
MAX_STAKE = 0.08
SENT_SIGNALS = {} # Previene duplicati

# ================= TELEGRAM =================
def send(msg):
    try:
        requests.post(
            f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": msg},
            timeout=10
        )
    except:
        pass

# ================= LOGICA DI ANALISI (ALGORITMO) =================
def analyze_pressure(h, a):
    """Calcola la pressione offensiva senza bisogno di modelli .pkl"""
    def get_val(stat, key):
        for s in stat.get("statistics", []):
            if key in s["type"].lower():
                return float(s["value"] or 0)
        return 0

    # Estrazione Dati
    h_shots = get_val(h, "shots on goal")
    a_shots = get_val(a, "shots on goal")
    h_danger = get_val(h, "dangerous attacks")
    a_danger = get_val(a, "dangerous attacks")
    h_poss = get_val(h, "possession")
    a_poss = get_val(a, "possession")

    # Calcolo Dominanza Netta (Casa vs Trasferta)
    # Se il valore è positivo, spinge la squadra in casa, se negativo quella in trasferta
    diff_shots = h_shots - a_shots
    diff_danger = h_danger - a_danger
    
    # Punteggio Dominanza (Formula proprietaria)
    dominance_score = (diff_shots * 3) + (diff_danger * 1.2) + ((h_poss - 50) * 0.5)
    
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
    except:
        return []

def get_odds():
    try:
        r = requests.get(
            "https://the-odds-api.com",
            params={"apiKey": ODDS_API_KEY, "regions": "eu", "markets": "h2h"},
            timeout=10
        )
        return r.json()
    except:
        return []

# ================= MAIN LOOP =================
def run():
    send("🚀 BET-BOT ONLINE (ALGORITMO STATISTICO ATTIVO)")
    print("Bot avviato...")

    while True:
        try:
            matches = get_matches()
            odds_list = get_odds()

            for m in matches:
                m_id = m["fixture"]["id"]
                
                # Evita duplicati (1 segnale per partita)
                if m_id in SENT_SIGNALS:
                    continue

                minute = m["fixture"]["status"]["elapsed"]
                if not minute or minute < 45 or minute > 80:
                    continue

                stats = m.get("statistics")
                if not stats or len(stats) < 2:
                    continue

                h_stat, a_stat = stats
                dom_score = analyze_pressure(h_stat, a_stat)

                # Identifica se c'è un dominio chiaro (> 20 di score)
                decision = None
                if dom_score > 22:
                    decision = f"🔥 DOMINIO CASA ({round(dom_score)})"
                elif dom_score < -22:
                    decision = f"🔥 DOMINIO OSPITE ({round(abs(dom_score))})"

                if decision:
                    home_n = m["teams"]["home"]["name"]
                    away_n = m["teams"]["away"]["name"]
                    
                    # Messaggio Telegram
                    msg = f"⚽ SIGNAL: {decision}\n\n🏆 {home_n} vs {away_n}\n⏰ Minuto: {minute}'\n📊 Pressione: {round(dom_score, 1)}\n\n⚠️ Verifica la quota live prima di entrare!"
                    send(msg)
                    SENT_SIGNALS[m_id] = True
                    print(f"Segnale inviato per {home_n}")

            time.sleep(60) # Controlla ogni minuto

        except Exception as e:
            print(f"Errore: {e}")
            time.sleep(20)

if __name__ == "__main__":
    run()
