import requests
import time

# --- CONFIGURAZIONE ---
API_KEY = "LA_TUA_API_KEY"
TELEGRAM_TOKEN = "IL_TUO_TOKEN"
CHAT_ID = "IL_TUO_CHAT_ID"

def analizza_live():
    # URL specifico per match IN-PLAY (Live)
    # Cerchiamo mercati Totali (Gol) e H2H
    url = f"https://the-odds-api.com{API_KEY}&regions=eu&markets=h2h,totals&oddsFormat=decimal"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if response.status_code != 200:
            print(f"❌ Errore API: {data.get('message', 'Errore sconosciuto')}")
            return

        for match in data:
            home = match['home_team']
            away = match['away_team']
            
            # Filtriamo solo i bookmaker che hanno quote aggiornate
            for bookie in match['bookmakers']:
                for market in bookie['markets']:
                    
                    # LOGICA GOL (OVER)
                    if market['key'] == 'totals':
                        for outcome in market['outcomes']:
                            # Esempio: Segnala Over 0.5 o 1.5 con quota interessante (pressione live)
                            if outcome['name'] == 'Over' and 1.75 <= outcome['price'] <= 2.50:
                                invia_telegram(
                                    f"⚽ **POSSIBILE GOL LIVE**\n"
                                    f"🏟️ {home} - {away}\n"
                                    f"📈 Mercato: {outcome['name']} {outcome['point']}\n"
                                    f"💰 Quota: {outcome['price']}\n"
                                    f"🏛️ Bookie: {bookie['title']}"
                                )

    except Exception as e:
        print(f"⚠️ Errore durante l'analisi: {e}")

def invia_telegram(testo):
    url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": testo, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

print("🚀 Scanner Live 2.0 Operativo...")
while True:
    analizza_live()
    # Aspettiamo 2 minuti tra una scansione e l'altra (bilanciamento crediti/velocità)
    time.sleep(120) 
