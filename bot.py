import requests
import time
import os
import json
from datetime import datetime

# =================================================================
# CONFIGURAZIONE (LEGGE DA RAILWAY VARIABLES)
# =================================================================
API_KEY_FOOTBALL = os.getenv("API_KEY_FOOTBALL")
RAW_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Pulizia automatica del token (rimuove 'bot' se inserito per errore)
TELEGRAM_TOKEN = RAW_TOKEN.replace("bot", "") if RAW_TOKEN else None

BANKROLL_INIZIALE = 50.0
TARGET_GIORNALIERO = 150.0
FILE_DATA = "bot_finanze.json"

def carica_dati():
    if os.path.exists(FILE_DATA):
        try:
            with open(FILE_DATA, "r") as f: return json.load(f)
        except: pass
    return {"bankroll": BANKROLL_INIZIALE, "daily_loss_count": 0, "last_trade_date": datetime.now().strftime("%Y-%m-%d")}

def salva_dati(dati):
    with open(FILE_DATA, "w") as f: json.dump(dati, f, indent=4)

def send_tg(msg):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("❌ Token o Chat_ID mancanti nelle variabili!")
        return False
    url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=15)
        if r.status_code != 200:
            print(f"❌ Errore Telegram API: {r.text}")
        return r.status_code == 200
    except Exception as e:
        print(f"❌ Errore connessione Telegram: {e}")
        return False

def analizza_dominio_reale(f_id):
    url = f"https://api-sports.io{f_id}"
    headers = {"x-apisports-key": API_KEY_FOOTBALL}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        if 'response' not in data or len(data['response']) < 2: return None
        
        res = data['response']
        def get_s(team_idx, name):
            for s in res[team_idx]['statistics']:
                if s['type'] == name: 
                    val = str(s['value'] or "0").replace('%','')
                    return int(val) if val.isdigit() else 0
            return 0

        h = {"tiri": get_s(0, 'Shots on Goal'), "att": get_s(0, 'Dangerous Attacks'), "pos": get_s(0, 'Ball Possession')}
        a = {"tiri": get_s(1, 'Shots on Goal'), "att": get_s(1, 'Dangerous Attacks'), "pos": get_s(1, 'Ball Possession')}

        if h['tiri'] >= a['tiri'] + 3 and h['att'] > a['att'] * 1.5: return {"side": "HOME", "name": "CASA", "odd": 1.50}
        if a['tiri'] >= h['tiri'] + 3 and a['att'] > h['att'] * 1.5: return {"side": "AWAY", "name": "TRASFERTA", "odd": 1.50}
        return None
    except: return None

def run_bot():
    dati = carica_dati()
    active_bet = None
    print("🚀 Avvio sistema...")
    send_tg(f"🤖 **SISTEMA ONLINE**\n💰 Bankroll: {dati['bankroll']}€")

    while True:
        try:
            dati = carica_dati()
            # 1. Controllo Bet Attiva
            if active_bet:
                r = requests.get(f"https://api-sports.io{active_bet['id']}", headers={"x-apisports-key": API_KEY_FOOTBALL}, timeout=10)
                res_data = r.json()
                if 'response' in res_data and res_data['response']:
                    res = res_data['response'][0]
                    if res['fixture']['status']['short'] in ['FT', 'AET', 'PEN']:
                        g_h, g_a = res['goals']['home'], res['goals']['away']
                        win = (active_bet['side'] == "HOME" and g_h > g_a) or (active_bet['side'] == "AWAY" and g_a > g_h)
                        profit = round(active_bet['stake'] * (active_bet['odd'] - 1), 2) if win else -active_bet['stake']
                        dati['bankroll'] = round(dati['bankroll'] + profit, 2)
                        send_tg(f"{'✅ WIN' if win else '❌ LOSS'}\n💰 Profitto: {profit}€\n🏦 Bank: {dati['bankroll']}€")
                        active_bet = None
                        salva_dati(dati)
            # 2. Ricerca Live
            else:
                r = requests.get("https://api-sports.io", headers={"x-apisports-key": API_KEY_FOOTBALL}, timeout=10)
                data = r.json()
                if 'response' in data:
                    for p in data['response']:
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
            print(f"⚠️ Errore: {e}")
            time.sleep(60)

if __name__ == "__main__":
    run_bot()
