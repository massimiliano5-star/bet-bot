import requests
import time
import sys

def log(msg):
    print(msg)
    sys.stdout.flush()

# --- CONFIGURAZIONE ---
API_KEY = "LA_TUA_API_KEY"
TOKEN = "IL_TUO_TOKEN"
CHAT_ID = "IL_TUO_ID"

log("🌍 GLOBAL SCANNER (1.20-1.50) AVVIATO...")

def analizza_tutti_i_campionati():
    # 'upcoming' recupera i match di tutte le leghe coperte dal tuo piano API
    url = f"https://the-odds-api.com{API_KEY}&regions=eu&markets=h2h,totals&oddsFormat=decimal"
    
    try:
        response = requests.get(url)
        if response.status_code != 200:
            log(f"❌ Errore API ({response.status_code}): {response.text}")
            return
            
        data = response.json()
        match_trovati = 0
        
        for match in data:
            home = match.get('home_team')
            away = match.get('away_team')
            league = match.get('sport_title')
            
            for bookie in match.get('bookmakers', []):
                for market in bookie.get('markets', []):
                    
                    # 1. ESITO FINALE (Vittoria casa/trasferta)
                    if market['key'] == 'h2h':
                        for outcome in market['outcomes']:
                            if 1.20 <= outcome['price'] <= 1.50:
                                invia_segnalazione(league, home, away, f"Vittoria {outcome['name']}", outcome['price'], bookie['title'])
                                match_trovati += 1

                    # 2. OVER 1.5 o 2.5 (Gol totali)
                    if market['key'] == 'totals':
                        for outcome in market['outcomes']:
                            if outcome['name'] == 'Over' and 1.20 <= outcome['price'] <= 1.50:
                                label = f"Over {outcome['point']} Gol"
                                invia_segnalazione(league, home, away, label, outcome['price'], bookie['title'])
                                match_trovati += 1

        log(f"✅ Scansione terminata. Segnali inviati: {match_trovati}")

    except Exception as e:
        log(f"⚠️ Errore critico: {e}")

def invia_segnalazione(league, home, away, mercato, quota, bookie):
    msg = (f"📍 **NUOVA OPPORTUNITÀ**\n"
           f"🏆 {league}\n"
           f"⚽ {home} - {away}\n"
           f"🎯 Segno: {mercato}\n"
           f"💰 Quota: {quota}\n"
           f"🏛️ Bookie: {bookie}")
    
    url = f"https://telegram.org{TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
    except:
        log("❌ Fallito invio messaggio Telegram")

# Ciclo di scansione ogni 2 ore (ottimale per i campionati minori e risparmio API)
while True:
    analizza_tutti_i_campionati()
    log("💤 In attesa della prossima scansione...")
    time.sleep(7200) 
