def analizza_tutti_i_campionati():
    url = "https://the-odds-api.com"
    
    # Parametri separati per evitare errori di "parsing" (scelta chirurgica)
    params = {
        'apiKey': API_KEY,
        'regions': 'eu',
        'markets': 'h2h,totals',
        'oddsFormat': 'decimal'
    }
    
    try:
        log("🔍 Controllo mercati in corso...")
        response = requests.get(url, params=params, timeout=15)
        
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
                    # Filtro Esito Finale (1.20 - 1.50)
                    if market['key'] == 'h2h':
                        for outcome in market['outcomes']:
                            if 1.20 <= outcome['price'] <= 1.50:
                                invia_segnalazione(league, home, away, f"Vittoria {outcome['name']}", outcome['price'], bookie['title'])
                                match_trovati += 1
                                
                    # Filtro Over (1.20 - 1.50)
                    if market['key'] == 'totals':
                        for outcome in market.get('outcomes', []):
                            if outcome['name'] == 'Over' and 1.20 <= outcome['price'] <= 1.50:
                                invia_segnalazione(league, home, away, f"Over {outcome['point']}", outcome['price'], bookie['title'])
                                match_trovati += 1

        log(f"✅ Scansione completata. Segnali inviati: {match_trovati}")

    except Exception as e:
        log(f"⚠️ Errore durante la scansione: {e}")
