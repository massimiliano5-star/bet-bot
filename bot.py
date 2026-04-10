import requests, time, datetime, sys

# Forza Railway a mostrare i log subito
sys.stdout.reconfigure(line_buffering=True)

# ===== CONFIG =====
TOKEN = "8649464893:AAHr0VkMebISJSqa-TKV0XIZxbZPjJ7LzyU"
CHAT_ID = "545852688"
OFFSET = -1 

print("--- [TEST] BOT IN MODALITÀ RISPOSTA RAPIDA ---")

def invia_tg(metodo, params=None):
    url = f"https://telegram.org{TOKEN}/{metodo}"
    try:
        r = requests.get(url, params=params, timeout=5)
        return r.json()
    except Exception as e:
        print(f"Errore rete: {e}")
        return None

# Reset iniziale
invia_tg("getUpdates", {"offset": OFFSET})
OFFSET = 0

def run():
    global OFFSET
    print("--- [TEST] BOT PRONTO ---")
    invia_tg("sendMessage", {"chat_id": CHAT_ID, "text": "✅ *TEST RISPOSTA RAPIDA*\nSe leggi questo, il bot è connesso. Scrivi `/status` ora!"})

    while True:
        try:
            # 1. LEGGI TELEGRAM (Ciclo continuo senza blocchi)
            updates = invia_tg("getUpdates", {"offset": OFFSET, "timeout": 5})
            if updates and updates.get("ok"):
                for u in updates["result"]:
                    OFFSET = u["update_id"] + 1
                    if "message" in u and "text" in u["message"]:
                        testo = u["message"].lower()
                        print(f"--- [LOG] Comando ricevuto: {testo} ---")
                        
                        if "/status" in testo:
                            invia_tg("sendMessage", {"chat_id": CHAT_ID, "text": "📊 *STATUS*: Funzionante al 100% ✅"})
            
            time.sleep(1) # Reattività massima
            
        except Exception as e:
            print(f"--- [ERRORE] {e} ---")
            time.sleep(2)

if __name__ == "__main__":
    run()
