import requests
import time
import sys

# Forza la scrittura immediata dei log su Railway
def log(msg):
    print(msg, flush=True)

# --- CONFIGURAZIONE (Inserisci i tuoi dati tra le virgolette) ---
API_KEY = "LA_TUA_API_KEY"
TOKEN = "IL_TUO_TELEGRAM_TOKEN"
CHAT_ID = "IL_TUO_CHAT_ID"

log("🚀 SCANNER DEFINITIVO (1.20-1.50) AVVIATO...")

def scansiona():
    log("🔍 Analisi mercati pre-match in corso...")
    url = "https://the-odds-api.com"
    params = {
        'apiKey': API_KEY,
        'regions': 'eu',
        'markets': 'h2h,totals',
        'oddsFormat': 'decimal'
    }
    
    try:
        r = requests.get(url, params=params, timeout=25)
        
        if r.status_code != 200:
            log(f"❌ Errore API: {r.status_code}")
            return

        data = r.json()
        counter = 0
        
        for match in data:
            home = match.get('home_team')
            away = match.get('away_team')
            league = match.get('sport_title')
            
            for bookie in match.get('bookmakers', []):
                for market in bookie.get('markets', []):
                    for outcome in market.get('outcomes', []):
                        
                        price = outcome.get('price')
                        
                        # --- FILTRO QUOTA 1.20 - 1.50 ---
                        if 1.20 <= price <= 1.50:
                            # Formattazione del nome del mercato
                            name = outcome.get('name')
                            if market['key'] == 'totals':
                                # Esempio: Over 1.5
                                label = f"{name} {outcome.get('point')} Gol"
                            else:
                                # Esempio: Vittoria Team A
                                label = f"Esito: {name}"

                            # Invia a Telegram
                            msg = (f"💎 **SAFE BET TROVATA**\n"
                                   f"🏆 {league}\n"
                                   f"⚽ {home} - {away}\n"
                                   f"🎯 {label}\n"
                                   f"💰 Quota: {price}\n"
                                   f"🏛️ Bookmaker: {bookie['title']}")
                            
                            t_url = f"https://telegram.org{TOKEN}/sendMessage"
                            requests.post(t_url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
                            counter += 1
        
        log(f"✅ Scansione completata. Segnali inviati: {counter}")

    except Exception as e:
        log(f"⚠️ Errore tecnico durante la scansione: {e}")

# --- LOOP DI ESECUZIONE OGNI 30 MINUTI ---
while True:
    scansiona()
    log("💤 Pausa di 30 minuti prima del prossimo controllo...")
    time.sleep(1800) 
