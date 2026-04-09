import os
import requests
import time
import sys

# Forza l'output immediato
def log(msg):
    print(msg)
    sys.stdout.flush()

# CONFIGURAZIONE (Usa le variabili che hai messo su Railway o scrivile qui)
TOKEN = "IL_TUO_TELEGRAM_TOKEN"
CHAT_ID = "IL_TUO_CHAT_ID"

log("🚀 TENTATIVO DI AVVIO...")

def test_telegram():
    url = f"https://telegram.org{TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": CHAT_ID, "text": "✅ BOT SVEGLIO! Railway è connesso."})
        log(f"Risultato test Telegram: {r.status_code}")
    except Exception as e:
        log(f"Errore test: {e}")

test_telegram()

while True:
    log("🤖 Bot in attesa di scommesse live...")
    time.sleep(60)
