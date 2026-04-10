import requests, time, sys

# Forza Railway a mostrare i log subito
sys.stdout.reconfigure(line_buffering=True)

# ===== CONFIG =====
TOKEN = "8649464893:AAHr0VkMebISJSqa-TKV0XIZxbZPjJ7LzyU"
CHAT_ID = "545852688"
OFFSET = -1 

print("--- [SISTEMA] Avvio con URL protetto ---")

def invia_richiesta(metodo, payload=None):
    """Costruisce l'URL in modo che Railway non possa sbagliarlo"""
    url = f"https://telegram.org{TOKEN}/{metodo}"
    try:
        # Usiamo POST per inviare i dati in modo più sicuro e stabile
        r = requests.post(url, json=payload, timeout=10)
        return r.json()
    except Exception as e:
        print(f"--- [LOG] Errore di rete: {e} ---")
        return None

# Reset iniziale della coda
invia_richiesta("getUpdates", {"offset": OFFSET})
print("--- [SISTEMA] Bot in ascolto... ---")

def run():
    global OFFSET
    # Primo messaggio di test
    invia_richiesta("sendMessage", {"chat_id": CHAT_ID, "text": "✅ *SISTEMA ONLINE*\nSe leggi questo, il parsing è risolto. Prova `/status`!"})

    while True:
        try:
            # 1. LEGGI TELEGRAM
            res = invia_richiesta("getUpdates", {"offset": OFFSET, "timeout": 5})
            if res and res.get("ok"):
                for u in res["result"]:
                    OFFSET = u["update_id"] + 1
                    if "message" in u and "text" in u["message"]:
                        testo = u["message"].lower()
                        print(f"--- [LOG] Ricevuto: {testo} ---")
                        
                        if "/status" in testo:
                            invia_richiesta("sendMessage", {"chat_id": CHAT_ID, "text": "📊 *STATUS*: Funzionante al 100%!"})
            
            time.sleep(2)
            
        except Exception as e:
            print(f"Errore loop: {e}")
            time.sleep(5)

if __name__ == "__main__":
    run()
