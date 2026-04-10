def read_msgs():
    global LAST_UPDATE_ID
    url = f"https://telegram.org{TOKEN}/getUpdates"
    
    try:
        res = requests.get(url, timeout=10).json()

        # CONTROLLO SICUREZZA: Se Telegram dà errore o il token è sbagliato
        if not res.get("ok"):
            print(f"⚠️ Errore API Telegram: {res.get('description')}")
            return []

        msgs = []
        for u in res.get("result", []): # .get evita il KeyError
            uid = u["update_id"]
            if LAST_UPDATE_ID is None or uid > LAST_UPDATE_ID:
                LAST_UPDATE_ID = uid
                if "message" in u:
                    msgs.append(u["message"].get("text", "").upper())
        return msgs

    except Exception as e:
        print(f"❌ Errore connessione: {e}")
        return []
