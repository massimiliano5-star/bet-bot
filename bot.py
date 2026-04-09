def scansiona():
    url = "https://the-odds-api.com"
    params = {
        'apiKey': API_KEY,
        'regions': 'eu',
        'markets': 'h2h', # Iniziamo solo con questo per testare
        'oddsFormat': 'decimal'
    }
    
    try:
        log("🔍 Analisi campionati in corso...")
        r = requests.get(url, params=params, timeout=20)
        
        # DEBUG: Se non è 200, stampiamo il motivo esatto
        if r.status_code != 200:
            log(f"❌ Errore API {r.status_code}: {r.text}")
            return

        # Tentativo di lettura JSON sicuro
        try:
            matches = r.json()
        except Exception:
            log("❌ L'API non ha restituito un JSON valido.")
            return

        if not matches:
            log("pessimo tempismo: Nessun match trovato al momento.")
            return

        counter = 0
        for m in matches:
            home = m.get('home_team')
            away = m.get('away_team')
            for b in m.get('bookmakers', []):
                for market in b.get('markets', []):
                    for out in market.get('outcomes', []):
                        if 1.20 <= out['price'] <= 1.50:
                            # INVIO TELEGRAM
                            msg = f"⚽ **SAFE BET**\n🏆 {m.get('sport_title')}\n🏟️ {home}-{away}\n🎯 {out['name']} @{out['price']}"
                            requests.post(f"https://telegram.org{TOKEN}/sendMessage", 
                                          json={"chat_id": CHAT_ID, "text": msg})
                            counter += 1
        
        log(f"✅ Scansione completata. Segnali: {counter}")

    except Exception as e:
        log(f"⚠️ Errore critico: {e}")
