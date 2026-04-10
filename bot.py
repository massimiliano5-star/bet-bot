import requests
import time
import os
import json
from datetime import datetime

# =================================================================
# CONFIGURAZIONE AUTOMATIZZATA (LEGGE DA RAILWAY VARIABLES)
# =================================================================
API_KEY_FOOTBALL = os.getenv("API_KEY_FOOTBALL")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# PARAMETRI ECONOMICI
BANKROLL_INIZIALE = 50.0
TARGET_GIORNALIERO = 150.0
FILE_DATA = "bot_finanze.json"

# Verifica che le variabili esistano
if not all([API_KEY_FOOTBALL, TELEGRAM_TOKEN, CHAT_ID]):
    print("❌ ERRORE: Variabili d'ambiente mancanti nel pannello Railway!")
    print(f"API_KEY: {'OK' if API_KEY_FOOTBALL else 'MANCANTE'}")
    print(f"TOKEN: {'OK' if TELEGRAM_TOKEN else 'MANCANTE'}")
    print(f"CHAT_ID: {'OK' if CHAT_ID else 'MANCANTE'}")

# =================================================================
# GESTIONE DATI E COMUNICAZIONE
# =================================================================
def carica_dati():
    if os.path.exists(FILE_DATA):
        try:
            with open(FILE_DATA, "r") as f: return json.load(f)
        except: pass
    return {
        "bankroll": BANKROLL_INIZIALE,
        "daily_loss_count": 0,
        "last_trade_date": datetime.now().strftime("%Y-%m-%d")
    }

def salva_dati(dati):
    with open(FILE_DATA, "w") as f: json.dump(dati, f, indent=4)

def send_tg(msg):
    url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, json=payload, timeout=15)
        return r.status_code == 200
    except Exception as e:
        print(f"❌ Errore Telegram: {e}")
        return False

# =================================================================
# ANALISI LIVE AVANZATA
# =================================================================
def analizza_dominio_reale(f_id):
    url = f"https://api-sports.io{f_id}"
    headers = {"x-apisports-key": API_KEY_FOOTBALL}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        res = r.json().get('response', [])
        if len(res) < 2: return None

        def get_s(team_idx, name):
            for s in res[team_idx]['statistics']:
                if s['type'] == name: 
                    val = str(s['value'] or "0").replace('%','')
                    return int(val) if val.isdigit() else 0
            return 0

        h = {"tiri": get_s(0, 'Shots on Goal'), "att": get_s(0, 'Dangerous Attacks'), "pos": get_s(0, 'Ball Possession')}
        a = {"tiri": get_s(1, 'Shots on Goal'), "att": get_s(1, 'Dangerous Attacks'), "pos": get_s(1, 'Ball Possession')}

        if h['tiri'] >= a['tiri'] + 3 and h['att'] > a['att'] * 1.5 and h['pos'] > 55:
            return {"side": "HOME", "name": "CASA", "odd": 1.50}
        if a['tiri'] >= h['tiri'] + 3 and a['att'] > h['att'] * 1.5 and a['pos'] > 55:
            return {"side": "AWAY", "name": "TRASFERTA", "odd": 1.50}
        return None
    except: return None

# =================================================================
# CORE LOOP
# =================================================================
def run_bot():
    dati = carica_dati()
    active_bet = None
    
    print("🚀 Avvio sistema con variabili d'ambiente...")
    if send_tg(f"🤖 **SISTEMA ELITE AUTOMATIZZATO**\n💰 Bankroll: {dati['bankroll']}€\n🎯 Target: {TARGET_GIORNALIERO}€/gg"):
        print("✅ Telegram collegato con successo!")
    else:
        print("❌ Errore collegamento Telegram. Verifica le variabili su Railway.")

    while True:
        try:
            dati = carica_dati()
            oggi = datetime.now().strftime("%Y-%m-%d")
            
            if dati.get('last_trade_date') != oggi:
                dati['daily_loss_count'] = 0
                dati['last_trade_date'] = oggi
                salva_dati(dati)

            if dati['daily_loss_count'] >= 2:
                time.sleep(3600)
                continue

            if active_bet:
                url = f"https://api-sports.io{active_bet['id']}"
                r = requests.get(url, headers={"x-apisports-key": API_KEY_FOOTBALL}, timeout=10)
                res = r.json()['response'][0]
                
                status = res['fixture']['status']['short']
                if status in ['FT', 'AET', 'PEN']:
                    g_h, g_a = res['goals']['home'], res['goals']['away']
                    win = (active_bet['side'] == "HOME" and g_h > g_a) or (active_bet['side'] == "AWAY" and g_a > g_h)
                    
                    profit = round(active_bet['stake'] * (active_bet['odd'] - 1), 2) if win else -active_bet['stake']
                    dati['bankroll'] = round(dati['bankroll'] + profit, 2)
                    dati['daily_loss_count'] = 0 if win else dati['daily_loss_count'] + 1
                    
                    esito = "✅ WIN" if win else "❌ LOSS"
                    send_tg(f"{esito}\n💰 Profitto: {profit}€\n🏦 Bank: {dati['bankroll']}€")
                    active_bet = None
                    salva_dati(dati)
            else:
                url_live = "https://api-sports.io"
                r = requests.get(url_live, headers={"x-apisports-key": API_KEY_FOOTBALL}, timeout=10)
                partite = r.json().get('response', [])
                
                for p in partite:
                    tempo = p['fixture']['status']['elapsed'] or 0
                    if 25 <= tempo <= 75:
                        analisi = analizza_dominio_reale(p['fixture']['id'])
                        if analisi:
                            stake = round(dati['bankroll'] * 0.10, 2) if dati['bankroll'] < 500 else round(dati['bankroll'] * 0.05, 2)
                            active_bet = {"id": p['fixture']['id'], "side": analisi['side'], "stake": stake, "odd": analisi['odd']}
                            send_tg(f"🔥 **SEGNALE**\n⚽ {p['teams']['home']['name']} - {p['teams']['away']['name']}\n🎯 Puntata: {analisi['name']}\n💰 Stake: {stake}€")
                            break

            time.sleep(300)
        except Exception as e:
            print(f"⚠️ Loop Error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    run_bot()
