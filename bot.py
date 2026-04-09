def scansiona():
    # 1. Lista dei gruppi di campionati da scansionare
    # 'soccer' copre i principali, 'upcoming' copre tutti i minori in arrivo
    endpoints = ["soccer", "upcoming"]
    
    for endpoint in endpoints:
        log(f"🔍 Scansione zona: {endpoint}...")
        url = f"https://the-odds-api.com{endpoint}/odds/"
        params = {
            'apiKey': API_KEY,
            'regions': 'eu',
            'markets': 'h2h,totals',
            'oddsFormat': 'decimal'
        }
        
        try:
            r = requests.get(url, params=params, timeout=30)
            if r.status_code != 200:
                log(f"❌ Errore API {endpoint}: {r.status_code}")
                continue

            try:
                data = r.json()
            except:
                log(f"⚠️ Risposta {endpoint} non valida. Salto zona.")
                continue

            counter = 0
            for match in data:
                home = match.get('home_team')
                away = match.get('away_team')
                league = match.get('sport_title')
                
                for bookie in match.get('bookmakers', []):
                    for market in bookie.get('markets', []):
                        for out in market.get('outcomes', []):
                            if 1.20 <= out.get('price', 0) <= 1.50:
                                label = out.get('name')
                                if market['key'] == 'totals':
                                    label = f"Over {out.get('point')} Gol"
                                
                                msg = f"🌍 **GLOBAL SAFE**\n🏆 {league}\n⚽ {home}-{away}\n🎯 {label} @{out['price']}"
                                requests.post(f"https://telegram.org{TOKEN}/sendMessage", 
                                              json={"chat_id": CHAT_ID, "text": msg})
                                counter += 1
            log(f"✅ Zona {endpoint} completata. Segnali: {counter}")
            # Piccola pausa tra una zona e l'altra per non stressare l'API
            time.sleep(2)

        except Exception as e:
            log(f"⚠️ Errore tecnico zona {endpoint}: {e}")
