import requests
import time
import sys

# Forza Railway a mostrare i log subito
sys.stdout.reconfigure(line_buffering=True)

# ===== CONFIG =====
TOKEN = "8649464893:AAHr0VkMebISJSqa-TKV0XIZxbZPjJ7LzyU"
CHAT_ID = "545852688"
OFFSET = -1 

print("--- [SISTEMA] Avvio Protocollo Sblocco Rete ---")

def chiama_telegram(metodo, payload=None):
    # Usiamo l'indirizzo completo e forziamo la chiusura della connessione ogni volta
    url = f"https://telegram.org{TOKEN}/{metodo}"
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Connection': 'close' # Forza Railway a non usare connessioni vecchie e bloccate
    }
    try:
        # Aumentiamo il timeout a 30 secondi per dare tempo alla rete Trial
        r = requests.post(url, data=payload, headers=headers, timeout=30)
        return r.json()
    except Exception as e:
        print(f"--- [LOG] Tentativo fallito, riprovo... ---")
        return None

# Reset iniziale della coda
chiama_telegram("getUpdates", {"offset": OFFSET})
print("--- [SISTEMA] In ascolto attivo... ---")

def run():
    global OFFSET
    # Primo messaggio di test
    chiama_telegram("sendMessage", {"chat_id": CHAT_ID, "text": "🚀 **SISTEMA SBLOCCATO**\nSe ricevi questo, abbiamo superato il blocco di Railway!"})

    while True:
        try:
            # 1. LEGGI TELEGRAM
            res = chiama_telegram("getUpdates", {"offset": OFFSET, "timeout": 20})
            
            if res and res.get("ok"):
                for u in res["result"]:
                    OFFSET = u["update_id"] + 1
                    if "message" in u and "text" in u["message"]:
                        testo = u["message"].lower()
                        print(f"--- [LOG] Comando: {testo} ---")
                        
                        if "/status" in testo:
                            chiama_telegram("sendMessage", {"chat_id": CHAT_ID, "text": "📊 **STATUS**: Operativo ✅"})
            
            time.sleep(5) # Pausa più lunga per non farsi bloccare dal firewall di Railway
            
        except Exception as e:
            time.sleep(10)

if __name__ == "__main__":
    run()
