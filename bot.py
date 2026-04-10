import requests, time, datetime, csv, os, pytz, sys

sys.stdout.reconfigure(line_buffering=True)

# ===== CONFIG =====
ODDS_API_KEY = "f0eaec5e8d2b7e2c0598b311b9e9aa32"
TOKEN = "8649464893:AAHr0VkMebISJSqa-TKV0XIZxbZPjJ7LzyU"
CHAT_ID = "545852688"
TZ = pytz.timezone('Europe/Rome')
OFFSET = -1 # Forza il reset della coda messaggi

print("--- [SISTEMA] AVVIO RESET E REAZIONE IMMEDIATA ---")

def invia_tg(metodo, params=None):
    url = f"https://telegram.org{TOKEN}/{metodo}"
    try:
        r = requests.get(url, params=params, timeout=10)
        return r.json()
    except: return None

# Pulizia iniziale della coda (fondamentale per sbloccarlo)
invia_tg("getUpdates", {"offset": OFFSET})
OFFSET = 0

def run():
    global OFFSET
    print("--- [SISTEMA] BOT PRONTO A RISPONDERE ---")
    invia_tg("sendMessage", {"chat_id": CHAT_ID, "text": "⚡️ *SISTEMA ONLINE*\nOra rispondo istantaneamente. Prova `/status`!"})

    while True:
        try:
            # 1. LETTURA MESSAGGI (Ciclo prioritario)
            updates = invia_tg("getUpdates", {"offset": OFFSET, "timeout": 5})
            if updates and updates.get("ok"):
                for u in updates["result"]:
                    OFFSET = u["update_id"] + 1
                    if "message" in u and "text" in u["message"]:
                        testo = u["message"].lower()
                        print(f"--- [LOG] Ricevuto: {testo} ---")
                        
                        if "/status" in testo:
                            invia_tg("sendMessage", {"chat_id": CHAT_ID, "text": "📊 *REPORT ELITE*\n💰 Bankroll: 50.00€\n✅ Status: Operativo\n⚽️ Match analizzati: 0"})
                        elif "/start" in testo:
                            invia_tg("sendMessage", {"chat_id": CHAT_ID, "text": "👋 Ciao! Sono attivo e monitoro i mercati."})

            # 2. ANALISI VELOCE (Solo se siamo in orario)
            ora = datetime.datetime.now(TZ).hour
            if 10 <= ora <= 23:
                # Esegui analisi solo ogni 5 cicli per non bloccare i comandi
                print("--- [ANALISI] Scansione quote... ---")
                # (Inseriremo qui la logica Odds API una volta testata la risposta)

            time.sleep(2) # Reazione quasi istantanea
        except Exception as e:
            print(f"--- [ERRORE] {e} ---")
            time.sleep(5)

if __name__ == "__main__":
    run()
