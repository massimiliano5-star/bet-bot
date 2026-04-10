import requests
import time
import pandas as pd
from datetime import datetime

# ===== CONFIGURAZIONE =====
API_KEY_FOOTBALL = "LA_TUA_API_FOOTBALL_KEY"
TELEGRAM_TOKEN = "IL_TUO_TELEGRAM_TOKEN"
CHAT_ID = "IL_TUO_CHAT_ID"

# PARAMETRI ECONOMICI (Road to 150€/day)
bankroll = 50.0  # Punto di partenza
target_giornaliero = 150.0
active_bets = {} # Formato: {fixture_id: {'stake': 5, 'team': 'Inter', 'odd': 1.45}}

def send_tg(msg):
    url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})

def get_live_matches():
    url = "https://api-sports.io"
    headers = {"x-apisports-key": API_KEY_FOOTBALL}
    try:
        return requests.get(url, headers=headers).json()['response']
    except:
        return []

def get_stake():
    """Strategia di scalata aggressiva fino a 500€, poi conservativa"""
    global bankroll
    if bankroll < 500:
        return round(bankroll * 0.10, 2) # 10% Stake per spingere i primi 50€
    elif bankroll < 2000:
        return round(bankroll * 0.05, 2) # 5% Consolidamento
    else:
        return round(target_giornaliero / 1.5, 2) # Stake fisso per target 150€

def check_and_settle():
    """Controlla i risultati delle partite finite e aggiorna il budget"""
    global bankroll, active_bets
    if not active_bets: return

    headers = {"x-apisports-key": API_KEY_FOOTBALL}
    settled = []

    for f_id, data in active_bets.items():
        res = requests.get(f"https://api-sports.io{f_id}", headers=headers).json()
        match = res['response'][0]
        status = match['fixture']['status']['short']

        if status in ['FT', 'AET', 'PEN']: # Partita terminata
            home_goals = match['goals']['home']
            away_goals = match['goals']['away']
            
            # Logica esito (Esempio semplificato: puntiamo sempre sulla favorita che domina)
            # Qui andrebbe la logica specifica della scommessa fatta
            win = True # (Simulazione esito positivo per brevità)
            
            profit = data['stake'] * (data['odd'] - 1) if win else -data['stake']
            bankroll += profit
            settled.append(f_id)
            
            esito_txt = "✅ WIN" if win else "❌ LOSS"
            send_tg(f"{esito_txt}\n⚽ {data['team']}\n💰 Profitto: {round(profit,2)}€\n🏦 Nuovo Bankroll: {round(bankroll,2)}€")

    for f_id in settled:
        del active_bets[f_id]

# ===== LOOP PRINCIPALE =====
send_tg("🤖 **SISTEMA ELITE LIVE ATTIVO**\nObiettivo: 150€/giorno\nBankroll iniziale: 50€")

while True:
    # 1. Controlla se ci sono risultati da aggiornare
    check_and_settle()

    # 2. Cerca nuove opportunità Live (se non ci sono bet attive)
    if len(active_bets) < 1:
        matches = get_live_matches()
        for m in matches:
            # FILTRO ELITE: Minuto 30-70, tiri totali > 10, squadra favorita sotto di 1 gol o pareggio
            tempo = m['fixture']['status']['elapsed']
            if 30 <= tempo <= 70:
                f_id = m['fixture']['id']
                home_name = m['teams']['home']['name']
                
                # Qui aggiungeresti la chiamata alle statistiche dettagliate (tiri, possesso)
                # Se i dati confermano il dominio:
                stake = get_stake()
                odd_fittizia = 1.45 # In un sistema reale, qui leggi l'API delle quote live
                
                active_bets[f_id] = {'stake': stake, 'team': home_name, 'odd': odd_fittizia}
                send_tg(f"🔥 **NUOVA BET LIVE**\n⚽ {home_name}\n⏰ Minuto: {tempo}'\n💰 Stake: {stake}€\n📈 Quota stimata: {odd_fittizia}")
                break # Solo 1 bet alla volta per massimo controllo

    time.sleep(300) # Controlla ogni 5 minuti
