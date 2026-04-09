def analizza_live():
    # URL ultra-semplice per testare se l'API ti risponde
    url = f"https://the-odds-api.com{API_KEY}"
    
    try:
        print("🔍 Tentativo di connessione API...")
        response = requests.get(url)
        
        # Stampiamo lo stato per capire se la chiave è valida
        print(f"📡 Stato API: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Connessione OK! Il tuo piano API funziona.")
            # Se arriviamo qui, possiamo rimettere la logica dei gol
        elif response.status_code == 401:
            print("❌ Errore: API_KEY non valida!")
        elif response.status_code == 429:
            print("❌ Errore: Hai finito i crediti gratuiti!")
        else:
            print(f"❌ Errore sconosciuto: {response.text}")

    except Exception as e:
        print(f"⚠️ Errore di rete: {e}")
