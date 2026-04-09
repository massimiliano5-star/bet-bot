def scansiona():
    log("🔍 Scansione Global (Tutti i campionati)...")
    
    # Usiamo 'upcoming' per prendere ogni match disponibile (Major e Minor leagues)
    url = "https://the-odds-api.com"
    
    params = {
        'apiKey': API_KEY,
        'regions': 'eu',
        'markets': 'h2h,totals',
        'oddsFormat': 'decimal'
    }
    
    try:
        r = requests.get(url, params=params, timeout=30)
        
        if r.status_code != 200:
            log(f"❌ Errore API {r.status_code}")
            return

        try:
            data = r.json()
        except:
            log("⚠️ Risposta non valida. Salto il giro.")
            return

        counter = 0
        for match in data:
            home = match.get('home_team')
            away = match.get('away_team')
            league = match.get('sport_title') # Qui vedrai il nome del campionato (es. 'Super League - China')
            
            for bookie in match.get('bookmakers', []):
                for market in bookie.get('markets', []):
                    for out in market.get('outcomes', []):
                        price = out.get('price')
                        
                        # FILTRO 1.20 - 1.50
                        if 1.20 <= price <= 1.50:
                            label = out.get('name')
                            if market['key'] == 'totals':
                                label = f"Over {out.get('point')} Gol"
                            
                            msg = (f"🌍 **GLOBAL SAFE BET**\n"
                                   f"🏆 {league}\n"
                                   f"⚽ {home} - {away}\n"
                                   f"🎯 {label} @{price}\n"
                                   f"🏛️ {bookie['title']}")
                            
                            requests.post(f"https://telegram.org{TOKEN}/sendMessage", 
                                          json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
                            counter += 1
        
        log(f"✅ Scansione completata. Segnali globali inviati: {counter}")

    except Exception as e:
        log(f"⚠️ Errore tecnico: {e}")
