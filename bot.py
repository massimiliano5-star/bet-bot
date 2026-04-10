import requests
import time
import datetime
import csv
import os
import pytz
import sys

# Forza Railway a mostrare i log immediatamente
sys.stdout.reconfigure(line_buffering=True)

# ===== 1. CONFIGURAZIONE =====
# Assicurati che queste chiavi siano esattamente tra le virgolette
ODDS_API_KEY = "f0eaec5e8d2b7e2c0598b311b9e9aa32"
FOOTBALL_API_KEY = "50c72696adfffd60c9540455af3b7f94"
TOKEN = "8649464893:AAHr0VkMebISJSqa-TKV0XIZxbZPjJ7LzyU"
CHAT_ID = "545852688"

# Impostazioni Sistema
FILE_CSV = "tracking.csv"
FUSO_ORARIO = pytz.timezone('Europe/Rome')
OFFSET_MESSAGGI = 0

print("--- [LOG] Inizializzazione Script Elite ---")

# ===== 2. CREAZIONE DATABASE CSV =====
if not os.path.exists(FILE_CSV):
    with open(FILE_CSV, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["data", "match", "quota", "stake", "esito", "profitto", "fixture_id"])
    print("--- [LOG] File tracking.csv creato ---")

# ===== 3. FUNZIONE INVIO TELEGRAM (CORRETTA) =====
def invia_messaggio(testo):
    # Costruzione URL manuale senza f-string per massima compatibilità
    url_base = "https://telegram.org" + TOKEN + "/sendMessage"
    dati = {
        "chat_id": CHAT_ID,
        "text": testo,
        "parse_mode": "Markdown"
    }
    try:
        r = requests.post(url_base, json=dati, timeout=10)
        print("--- [LOG] Telegram Status: " + str(r.status_code) + " ---")
        return r.json()
    except Exception as e:
        print("--- [ERRORE] Invio fallito: " + str(e) + " ---")
        return None

# ===== 4. FUNZIONE ANALISI QUOTE =====
def cerca_scommesse():
    # Analizza solo se siamo tra le 10:00 e le 23:59
    ora_ora = datetime.datetime.now(FUSO_ORARIO).hour
    if ora_ora < 10:
        return None

    print("--- [LOG] Scansione mercati in corso... ---")
    url_odds = "https://the-odds-api.com" + ODDS_API_KEY + "&regions=eu&markets=h2h"
    
    try:
        res = requests.get(url_odds, timeout=15).json()
        for partita in res:
            try:
                # Navighiamo nei dati per trovare la favorita
                bookmaker = partita["bookmakers"][0]
                mercato = bookmaker["markets"][0]
                esiti = sorted(mercato["outcomes"], key=lambda x: x['price'])
                
                favorito = esiti[0] # Squadra con quota più bassa
                quota = favorito["price"]
                
                # FILTRO ELITE: Quota tra 1.25 e 1.45
                if 1.25 <= quota <= 1.45:
                    return {
                        "match": partita["home_team"] + " vs " + partita["away_team"],
                        "team": favorito["name"],
                        "quota": quota
                    }
            except:
                continue
    except Exception as e:
        print("--- [ERRORE] Analisi quote: " + str(e) + " ---")
    return None

# ===== 5. LOOP PRINCIPALE =====
def esegui():
    global OFFSET_MESSAGGI
    print("--- [SISTEMA] BOT OPERATIVO AL 100% ---")
    invia_messaggio("🚀 *SISTEMA ELITE AVVIATO*\nIl bot è ora online su Railway.\nScrivi `/status` per il report.")

    while True:
        try:
            # A. Controllo Comandi Telegram
            url_updates = "https://telegram.org" + TOKEN + "/getUpdates?offset=" + str(OFFSET_MESSAGGI)
            aggiornamenti = requests.get(url_updates, timeout=10).json()
            
            if aggiornamenti.get("ok"):
                for item in aggiornamenti.get("result", []):
                    OFFSET_MESSAGGI = item["update_id"] + 1
                    testo_ricevuto = item.get("message", {}).get("text", "").lower()
                    
                    if "/status" in testo_ricevuto:
                        invia_messaggio("📊 *REPORT ELITE*\n💰 Bilancio: 50.00€\n✅ Match: 0\n🚀 Target: 150€")

            # B. Ricerca Scommesse
            segnale = cerca_scommesse()
            if segnale:
                msg_bet = "🔥 *NUOVO SEGNALE*\n🏟 " + segnale["match"] + "\n👉 Punta: " + segnale["team"] + "\n📈 Quota: " + str(segnale["quota"])
                invia_messaggio(msg_bet)
                # Salvataggio semplice nel CSV
                with open(FILE_CSV, "a", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), segnale["match"], segnale["quota"], 5.0, "PENDING", 0, "ID_LIVE"])

            # Aspetta 2 minuti prima del prossimo ciclo
            time.sleep(120)

        except Exception as e:
            print("--- [LOOP ERRORE] " + str(e) + " ---")
            time.sleep(30)

if __name__ == "__main__":
    esegui()
