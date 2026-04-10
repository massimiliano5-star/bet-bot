import requests, time, datetime, csv, os, pytz, sys

sys.stdout.reconfigure(line_buffering=True)

# ===== CONFIG =====
ODDS_API_KEY = "f0eaec5e8d2b7e2c0598b311b9e9aa32"
TOKEN = "8649464893:AAHr0VkMebISJSqa-TKV0XIZxbZPjJ7LzyU"
CHAT_ID = "545852688"
TZ = pytz.timezone('Europe/Rome')
OFFSET = -1 

print("--- [SISTEMA] AVVIO CORRETTO CON PRIORITÀ TELEGRAM ---")

def invia_tg(metodo, params=None):
    url = f"https://telegram.org{TOKEN}/{metodo}"
    try:
        r = requests.get(url, params=params, timeout=10)
        return r.json()
    except: return None

# Reset iniziale della coda
invia_tg("getUpdates", {"offset": OFFSET})
OFFSET = 0

def run():
    global OFFSET
    ultimo_controllo_quote = 0 # Timer per non intasare il bot
    
    print("--- [SISTEMA] BOT PRONTO ---")
    invia_tg("sendMessage", {"chat_id": CHAT_ID, "text": "⚡️ *SISTEMA SBLOCCATO*\nAdesso i comandi hanno la priorità. Prova `/status`!"})

    while True:
        try:
            # 1. LEGGI TELEGRAM (Sempre prioritario)
            updates = invia_tg("getUpdates", {"offset": OFFSET, "timeout": 5})
            if updates and updates.get("ok"):
                for u in updates["result"]:
                    OFFSET = u["update_id"] + 1
                    if "message" in u and "text" in u["message"]:
                        testo = u["message"].lower()
                        print(f"--- [LOG] Ricevuto comando: {testo} ---")
                        
                        if "/status" in testo:
                            invia_tg("sendMessage", {"chat_id": CHAT_ID, "text": "📊 *REPORT ELITE*\n💰 Bankroll: 50.00€\n✅ Status: Operativo e Sbloccato"})

            # 2. ANALISI QUOTE (Solo ogni 5 minuti / 300 secondi)
            tempo_attuale = time.time()
            if tempo_attuale - ultimo_controllo_quote > 300:
                print("--- [ANALISI] Scansione quote (Ogni 5 min)... ---")
                # (Qui il bot fa il suo lavoro di ricerca)
                ultimo_controllo_quote = tempo_attuale

            time.sleep(2) # Pausa breve per essere reattivo su Telegram
            
        except Exception as e:
            print(f"--- [ERRORE] {e} ---")
            time.sleep(5)

if __name__ == "__main__":
    run()
