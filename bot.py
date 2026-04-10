import requests
import time
import os
import json
from datetime import datetime

# =================================================================
# CONFIGURAZIONE (INSERISCI I TUOI DATI)
# =================================================================
API_KEY_FOOTBALL = "LA_TUA_API_FOOTBALL_KEY"
TELEGRAM_TOKEN = "IL_TUO_TELEGRAM_TOKEN"
CHAT_ID = "IL_TUO_CHAT_ID"  # Deve essere un numero, es: 12345678

# PARAMETRI ECONOMICI
BANKROLL_INIZIALE = 50.0
TARGET_GIORNALIERO = 150.0
FILE_DATA = "bot_finanze.json"

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
        "history": [],
        "daily_loss_count": 0,
        "last_trade_date": datetime.now().strftime("%Y-%m-%d")
    }

def salva_dati(dati):
    with open(FILE_DATA, "w") as f: json.dump(dati, f, indent=4)

def send_tg(msg):
    url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code != 200:
            print(f"❌ Errore API Telegram: {r.text}")
        return r.status_code == 200
    except Exception as e:
        print(f"❌ Errore connessione Telegram: {e}")
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

        # LOGICA DI SELEZIONE ELITE
        if h['tiri'] >= a['tiri'] + 3 and h['att'] > a['att'] * 1.5 and h['pos'] > 55:
            return {"side": "HOME", "name": "CASA", "odd": 1.50}
        if a['tiri'] >= h['tiri'] + 3 and a['att'] > h['att'] * 1.5 and a['pos'] > 55:
            return {"side": "AWAY", "name": "TRASFERTA", "odd": 1.50}
        return None
    except Exception as e:
        print(f"⚠️ Errore analisi match {f_id}: {e}")
        return None

# =================================================================
# CORE LOOP
# =================================================================
def run_bot():
    dati = carica_dati()
    active_bet = None
    
    print("🚀 Bot in fase di avvio...")
    check_tg = send_tg(f"🤖 **SISTEMA ELITE LIVE ONLINE**\n💰 Bankroll attuale: {dati['bankroll']}€\n🎯 Obiettivo: {TARGET_GIORNALIERO}€/gg")
    
    if not check_tg:
        print("🚨 ATTENZIONE: Il bot non riesce a inviare messaggi a Telegram. Controlla Token e Chat ID.")

    while True:
        try:
            dati = carica_dati()
            
            # Reset giornaliero dello stop-loss
            oggi = datetime.now().strftime("%Y-%m-%d")
            if dati.get('last_trade_date') != oggi:
                dati['daily_loss_count'] = 0
                dati['last_trade_date'] = oggi
                salva_dati(dati)

            # 1. PROTEZIONE STOP-LOSS
            if dati['daily_loss_count'] >= 2:
                time.sleep(3600) # Controlla ogni ora se può ripartire
                continue

            # 2. CONTROLLO BET ATTIVA
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
                    
                    esito_icona = "✅ WIN" if win else "❌ LOSS"
                    send_tg(f"{esito_icona}\n💰 Profitto: {profit}€\n🏦 Nuovo Bankroll: {dati['bankroll']}€")
                    active_bet = None
                    salva_dati(dati)

            # 3. RICERCA LIVE
            else:
                url_live = "https://api-sports.io"
                r = requests.get(url_live, headers={"x-apisports-key": API_KEY_FOOTBALL}, timeout=10)
                partite = r.json().get('response', [])
                
                for p in partite:
                    tempo = p['fixture']['status']['elapsed'] or 0
                    if 25 <= tempo <= 75:
                        analisi = analizza_dominio_reale(p['fixture']['id'])
                        if analisi:
                            # Calcolo Stake (10% se sotto i 500€ per scalare)
                            stake = round(dati['bankroll'] * 0.10, 2) if dati['bankroll'] < 500 else round(dati['bankroll'] * 0.05, 2)
                            
                            active_bet = {
                                "id": p['fixture']['id'],
                                "side": analisi['side'],
                                "stake": stake,
                                "odd": analisi['odd']
                            }
                            
                            send_tg(f"🔥 **SEGNALE RILEVATO**\n⚽ {p['teams']['home']['name']} - {p['teams']['away']['name']}\n🎯 Puntata: {analisi['name']}\n💰 Stake: {stake}€\n⏰ Minuto: {tempo}'")
                            break

            time.sleep(300) # Ciclo ogni 5 minuti

        except Exception as e:
            print(f"🚨 Errore nel loop principale: {e}")
            time.sleep(60)

if __name__ == "__main__":
    run_bot()
