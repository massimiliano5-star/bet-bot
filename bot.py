import requests
import time
import sys

# Forza Railway a mostrare i log subito
sys.stdout.reconfigure(line_buffering=True)

# ===== CONFIG =====
TOKEN = "8649464893:AAHr0VkMebISJSqa-TKV0XIZxbZPjJ7LzyU"
CHAT_ID = "545852688"
OFFSET = -1 

print("--- [SISTEMA] Avvio con Protocollo di Sicurezza ---")

def chiama_telegram(metodo, payload=None):
    """Costruisce l'URL in modo che Railway non possa 'spezzarlo'"""
    # Usiamo la base URL pulita
    url = f"https://telegram.org{TOKEN}/{metodo}"
    try:
        # Usiamo una richiesta POST che è molto più stabile su Railway
        r = requests.post(url, data=payload, timeout=15)
        return r.json()
    except Exception as e:
        print(f"--- [ERRORE DI RETE] ---")
        return None

# Reset iniziale della coda messaggi
chiama_telegram("getUpdates", {"offset": OFFSET})
print("--- [SISTEMA] Bot in ascolto attivo... ---")

def run():
    global OFFSET
    # Primo messaggio di test per confermare la connessione
    chiama_telegram("sendMessage", {"chat_id": CHAT_ID, "text": "✅ **SISTEMA ELITE ONLINE**\nSe ricevi questo, il problema di Railway è risolto!\n\nProva il comando: `/status`"})

    while True:
        try:
            # 1. LEGGI TELEGRAM
            res = chiama_telegram("getUpdates", {"offset": OFFSET, "timeout": 10})
            if res and res.get("ok"):
                for u in res["result"]:
                    OFFSET = u["update_id"] + 1
                    if "message" in u and "text" in u["message"]:
                        testo = u["message"].lower()
                        print(f"--- [LOG] Comando ricevuto: {testo} ---")
                        
                        if "/status" in testo:
                            chiama_telegram("sendMessage", {"chat_id": CHAT_ID, "text": "📊 **STATUS**: Operativo al 100% ✅"})
            
            time.sleep(2) # Reattività massima
            
        except Exception as e:
            print(f"Errore nel loop: {e}")
            time.sleep(5)

if __name__ == "__main__":
    run()
