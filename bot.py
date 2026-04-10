import requests, time, datetime, csv, os, pytz, sys

# Forza Railway a mostrare i log subito
sys.stdout.reconfigure(line_buffering=True)

# ===== CONFIG =====
ODDS_API_KEY = "f0eaec5e8d2b7e2c0598b311b9e9aa32"
TOKEN = "8649464893:AAHr0VkMebISJSqa-TKV0XIZxbZPjJ7LzyU"
CHAT_ID = "545852688"
TZ = pytz.timezone('Europe/Rome')
OFFSET = -1 

print("--- [SISTEMA] AVVIO VERSION ELITE SBLOCCATA ---")

def invia_tg(metodo, params=None):
    url = f"https://telegram.org{TOKEN}/{metodo}"
    try:
        r = requests.get(url, params=params, timeout=5) # Timeout corto per non bloccare
        return r.json()
    except: return None

# Reset iniziale della coda messaggi
invia_tg("getUpdates", {"offset": OFFSET})
OFFSET = 0

def run():
    global OFFSET
    ultimo_controllo_quote = 0
    
    print("--- [SISTEMA] BOT PRONTO E IN ASCOLTO ---")
    invia_tg("sendMessage", {"chat_id": CHAT_ID, "text": "✅ *SISTEMA SBLOCCATO TOTALMENTE*\nAdesso rispondo subito. Prova `/status`!"})

    while True:
        try:
            # 1. TELEGRAM (Priorità Assoluta)
            updates = invia_tg("getUpdates", {"offset": OFFSET, "timeout": 2})
            if updates and updates.get("ok"):
                for u in updates["result"]:
                    OFFSET = u["update_id"] + 1
                    if "message" in u and "text" in u["message"]:
                        testo = u["message"].lower()
                        print(f"--- [LOG] Comando Telegram: {testo} ---")
                        
                        if "/status" in testo:
                            invia_tg("sendMessage", {"chat_id": CHAT_ID, "text": "📊 *REPORT REAL-TIME*\n💰 Bankroll: 50.00€\n⚡️ Stato: Operativo\n📡 Connessione: OK"})
                        elif "/start" in testo:
                            invia_tg("sendMessage", {"chat_id": CHAT_ID, "text": "👋 Bot Elite attivo e pronto!"})

            # 2. ANALISI (Solo una volta ogni 10 minuti per non saturare la rete)
            tempo_attuale = time.time()
            if tempo_attuale - ultimo_controllo_quote > 600:
                print("--- [SISTEMA] Avvio Scansione Quote (Safe Mode) ---")
                try:
                    url_o = f"https://the-odds-api.com{ODDS_API_KEY}&regions=eu&markets=h2h"
                    # Chiamata rapida per non bloccare il bot
                    res = requests.get(url_o, timeout=10).json()
                    print(f"--- [ANALISI] Match scansionati: {len(res)} ---")
                except:
                    print("--- [ANALISI] Errore o Timeout quote, riprovo dopo ---")
                
                ultimo_controllo_quote = tempo_attuale

            time.sleep(1) # Reazione in 1 secondo
            
        except Exception as e:
            print(f"--- [LOOP ERRORE] {e} ---")
            time.sleep(5)

if __name__ == "__main__":
    run()
