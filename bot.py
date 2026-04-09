import requests
import time

# --- CONFIGURAZIONE ---
API_KEY = "LA_TUA_API_KEY"
TELEGRAM_TOKEN = "IL_TUO_TOKEN"
CHAT_ID = "IL_TUO_CHAT_ID"

def analizza_live():
    # Recuperiamo i match in corso (Live)
    # Nota: Usiamo i mercati h2h e totals per l'analisi
    url = f"https://the-odds-api.com{API_KEY}&regions=eu&markets=h2h,totals&oddsFormat=decimal"
    
    try:
        response = requests.get(url).json()
        
        for match in response:
            home_team = match['home_team']
            away_team = match['away_team']
            
            # Qui estraiamo le quote per trovare anomalie
            # In una versione avanzata qui integreremo i dati dei tiri/corner
            # se il tuo piano API include gli "event-data"
            
            for bookie in match['bookmakers']:
                for market in bookie['markets']:
                    if market['key'] == 'totals':
                        for outcome in market['outcomes']:
                            # ESEMPIO: Se la quota per l'Over 0.5 o Over 1.5 è tra 1.80 e 2.20
                            # ed è un momento "caldo" del match
                            if outcome['name'] == 'Over' and 1.80 <= outcome['price'] <= 2.30:
                                messaggio = (
                                    f"🔥 **SEGNALE LIVE: POSSIBILE GOL**\n"
                                    f"⚽ {home_team} vs {away_team}\n"
                                    f"📈 Mercato: {outcome['name']} {outcome['point']}\n"
                                    f"💰 Quota: {outcome['price']}\n"
                                    f"🏛️ Bookie: {bookie['title']}"
                                )
                                invia_telegram(messaggio)
                                
    except Exception as e:
        print(f"Errore scansione: {e}")

def invia_telegram(testo):
    url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": testo, "parse_mode": "Markdown"})

print("🚀 Scanner Live Avviato...")
while True:
    analizza_live()
    time.sleep(300) # Scansiona ogni 5 minuti per evitare di finire i crediti API
