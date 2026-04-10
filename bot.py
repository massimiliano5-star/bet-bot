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
CHAT_ID = "IL_TUO_CHAT_ID"

# PARAMETRI ECONOMICI
BANKROLL_INIZIALE = 50.0
TARGET_GIORNALIERO = 150.0
FILE_DATA = "bot_finanze.json"

# =================================================================
# GESTIONE DATI E FINANZE
# =================================================================
def carica_dati():
    if os.path.exists(FILE_DATA):
        with open(FILE_DATA, "r") as f: return json.load(f)
    return {
        "bankroll": BANKROLL_INIZIALE,
        "history": [],
        "daily_loss_count": 0,
        "last_trade_date": ""
    }

def salva_dati(dati):
    with open(FILE_DATA, "w") as f: json.dump(dati, f, indent=4)

def send_tg(msg):
    url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
    try: requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
    except: print("Errore invio Telegram")

# =================================================================
# CERVELLO ANALITICO (LIVE STATS)
# =================================================================
def analizza_dominio_reale(f_id):
    url = f"https://api-sports.io{f_id}"
    headers = {"x-apisports-key": API_KEY_FOOTBALL}
    try:
        res = requests.get(url, headers=headers).json()['response']
        if len(res) < 2: return None

        def get_s(team_idx, name):
            for s in res[team_idx]['statistics']:
                if s['type'] == name: return int(str(s['value'] or 0).replace('%',''))
            return 0

        # Statistiche Casa vs Trasferta
        stats = {
            "h": {"tiri": get_s(0, 'Shots on Goal'), "att": get_s(0, 'Dangerous Attacks'), "pos": get_s(0, 'Ball Possession')},
            "a": {"tiri": get_s(1, 'Shots on Goal'), "att": get_s(1, 'Dangerous Attacks'), "pos": get_s(1, 'Ball Possession')}
        }

        # FILTRO SICUREZZA: Dominio schiacciante
        if stats['h']['tiri'] >= stats['a']['tiri'] + 3 and stats['h']['att'] > stats['a']['att'] * 1.5:
            return {"side": "HOME", "name": "CASA", "odd": 1.45} # Quota media stimata live
        if stats['a']['tiri'] >= stats['h']['tiri'] + 3 and stats['a']['att'] > stats['h']['att'] * 1.5:
            return {"side": "AWAY", "name": "TRASFERTA", "odd": 1.45}
        return None
    except: return None

# =================================================================
# CORE LOGIC
# =================================================================
def run_bot():
    dati = carica_dati()
    active_bet = None
    
    send_tg(f"🚀 **SISTEMA ELITE AVVIATO**\n💰 Bankroll: {dati['bankroll']}€\n🎯 Target: {TARGET_GIORNALIERO}€/gg")

    while True:
        dati = carica_dati()
        
        # 1. STOP-LOSS SICUREZZA
        if dati['daily_loss_count'] >= 2:
            send_tg("⚠️ **STOP-LOSS ATTIVO**: 2 perdite consecutive. Mi fermo per sicurezza.")
            time.sleep(28800) # Fermo 8 ore
            dati['daily_loss_count'] = 0
            salva_dati(dati)
            continue

        # 2. CONTROLLO ESITO BET ATTIVA
        if active_bet:
            url = f"https://api-sports.io{active_bet['id']}"
            res = requests.get(url, headers={"x-apisports-key": API_KEY_FOOTBALL}).json()['response'][0]
            
            if res['fixture']['status']['short'] in ['FT', 'AET', 'PEN']:
                g_h, g_a = res['goals']['home'], res['goals']['away']
                win = (active_bet['side'] == "HOME" and g_h > g_a) or (active_bet['side'] == "AWAY" and g_a > g_h)
                
                profit = active_bet['stake'] * (active_bet['odd'] - 1) if win else -active_bet['stake']
                dati['bankroll'] += profit
                dati['daily_loss_count'] = 0 if win else dati['daily_loss_count'] + 1
                
                msg = f"{'✅ WIN' if win else '❌ LOSS'}\n💰 Profitto: {round(profit,2)}€\n🏦 Bank: {round(dati['bankroll'],2)}€"
                send_tg(msg)
                active_bet = None
                salva_dati(dati)

        # 3. RICERCA NUOVA OPPORTUNITÀ (Solo se non ho bet attive)
        else:
            url_live = "https://api-sports.io"
            partite = requests.get(url_live, headers={"x-apisports-key": API_KEY_FOOTBALL}).json()['response']
            
            for p in partite:
                tempo = p['fixture']['status']['elapsed']
                if 25 <= tempo <= 70: # Finestra di tempo ottimale
                    analisi = analizza_dominio_reale(p['fixture']['id'])
                    
                    if analisi:
                        # CALCOLO STAKE ADATTIVO
                        if dati['bankroll'] < 500: stake = round(dati['bankroll'] * 0.10, 2) # Aggressivo per scalata
                        else: stake = round(dati['bankroll'] * 0.05, 2) # Conservativo
                        
                        active_bet = {
                            "id": p['fixture']['id'],
                            "side": analisi['side'],
                            "stake": stake,
                            "odd": analisi['odd']
                        }
                        
                        send_tg(f"🔥 **BET IDENTIFICATA**\n⚽ {p['teams']['home']['name']} vs {p['teams']['away']['name']}\n🎯 Puntata su: {analisi['name']}\n💰 Stake: {stake}€\n⏰ Minuto: {tempo}'")
                        break # Gestisce una partita alla volta

        time.sleep(300) # Controllo ogni 5 minuti

if __name__ == "__main__":
    run_bot()
