def analizza_live():
    # URL semplificato: chiediamo solo i Totali (Over/Under) che sono quelli che ti interessano
    url = f"https://the-odds-api.com{API_KEY}&regions=eu&markets=totals&oddsFormat=decimal"
    
    try:
        print("🔍 Controllo mercati live...")
        response = requests.get(url)
        
        # Se l'API risponde con un errore di autorizzazione o piano
        if response.status_code != 200:
            print(f"❌ Errore API ({response.status_code}): {response.text}")
            return

        data = response.json()
        
        # Se non ci sono partite in questo momento
        if not data:
            print("pessimo tempismo: nessun match trovato ora.")
            return

        for match in data:
            home = match.get('home_team')
            away = match.get('away_team')
            
            for bookie in match.get('bookmakers', []):
                for market in bookie.get('markets', []):
                    if market['key'] == 'totals':
                        for outcome in market.get('outcomes', []):
                            # Filtro: Over tra 1.80 e 2.50
                            if outcome['name'] == 'Over' and 1.80 <= outcome['price'] <= 2.50:
                                msg = (f"⚽ **LIVE SIGNAL**\n"
                                       f"🏟️ {home} - {away}\n"
                                       f"📈 {outcome['name']} {outcome['point']}\n"
                                       f"💰 Quota: {outcome['price']}\n"
                                       f"🏛️ {bookie['title']}")
                                invia_telegram(msg)
                                print(f"✅ Segnale inviato per {home}")

    except Exception as e:
        print(f"⚠️ Errore critico: {e}")
