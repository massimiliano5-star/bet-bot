import requests, time, datetime, csv, os, pytz, sys

sys.stdout.reconfigure(line_buffering=True)

# ===== CONFIG =====
ODDS_API_KEY = "f0eaec5e8d2b7e2c0598b311b9e9aa32"
FOOTBALL_API_KEY = "50c72696adfffd60c9540455af3b7f94"
TOKEN = "8649464893:AAHr0VkMebISJSqa-TKV0XIZxbZPjJ7LzyU"
CHAT_ID = "545852688"
TZ = pytz.timezone('Europe/Rome')
OFFSET = -1 # RESET FORZATO PER LEGGERE SOLO I NUOVI MESSAGGI

print("--- [SISTEMA] AVVIO RESET MESSAGGI... ---")

def invia_tg(metodo, params=None):
    url = f"https://telegram.org{TOKEN}/{metodo}"
    try:
        r = requests.get(url, params=params, timeout=20)
        return r.json()
    except: return None

def run():
    global OFFSET
    # Primo comando per pulire la coda messaggi di Telegram
    invia_tg("getUpdates", {"offset": OFFSET})
    OFFSET = 0 # Riporta a zero per iniziare il ciclo normale
    
    print("--- [SISTEMA] ORA IN ASCOLTO REAL-TIME ---")
    invia_tg("sendMessage", {"chat_id": CHAT_ID, "text": "⚡️ *SISTEMA RESETTATO E PRONTO*\nScrivi `/status` ADESSO.", "parse_mode": "Markdown"})

    while True:
        try:
            # 1. LETTURA MESSAGGI
            updates = invia_tg("getUpdates", {"offset": OFFSET, "timeout": 10})
            if updates and updates.get("ok"):
                for u in updates["result"]:
                    OFFSET = u["update_id"] + 1
                    if "message" in u and "text" in u["message"]:
                        testo = u["message"].lower()
                        print(f"--- [LOG] Comando ricevuto: {testo} ---")
                        
                        if "/status" in testo:
                            invia_tg("sendMessage", {"chat_id": CHAT_ID, "text": "📊 *REPORT ATTIVO*\n💰 Bankroll: 50.00€\n✅ Status: Operativo"})
            
            # 2. RICERCA BET (Semplice)
            # (Ho rimosso momentaneamente l'analisi per testare solo la risposta)
            
            time.sleep(5) # Ciclo velocissimo per il test di risposta
        except Exception as e:
            print(f"--- [ERRORE] {e} ---")
            time.sleep(5)

if __name__ == "__main__":
    run()
