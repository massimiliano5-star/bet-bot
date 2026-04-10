import requests
import time
import os
import json
from datetime import datetime

# =================================================================
# CONFIGURAZIONE (DA RAILWAY VARIABLES)
# =================================================================
API_KEY_FOOTBALL = os.getenv("API_KEY_FOOTBALL")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

BANKROLL_INIZIALE = 50.0
TARGET_GIORNALIERO = 150.0
FILE_DATA = "bot_finanze.json"

def carica_dati():
    default = {"bankroll": BANKROLL_INIZIALE, "daily_loss_count": 0, "last_trade_date": datetime.now().strftime("%Y-%m-%d")}
    if not os.path.exists(FILE_DATA):
        return default
    try:
        with open(FILE_DATA, "r") as f:
            content = f.read().strip()
            if not content: return default
            return json.loads(content)
    except:
        return default

def salva_dati(dati):
    try:
        with open(FILE_DATA, "w") as f:
            json.dump(dati, f, indent=4)
    except Exception as e:
        print(f"⚠️ Errore salvataggio: {e}")

def send_tg(msg):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("❌ Variabili Telegram mancanti!")
        return False
    
    # Pulizia totale del token
    token = str(TELEGRAM_TOKEN).strip().replace("bot", "")
    url = f"https://telegram.org{token}/sendMessage"
    
    try:
        r = requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=20)
        if r.status_code != 200:
            print(f"❌ Telegram API Error: {r.text}")
        return r.status_code == 200
    except Exception as e:
        print(f"❌ Errore connessione: {e}")
        return False

def analizza_dominio_reale(f_id):
    url = f"https://api-sports.io{f_id}"
    headers = {"x-apisports-key": API_KEY_FOOTBALL}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        res = data.get('response', [])
        if len(res) < 2: return None
        
        def get_s(team_idx, name):
            for s in res[team_idx]['statistics']:
                if s['type'] == name: 
                    val = str(s['value'] or "0").replace('%','')
                    return int(val) if val.isdigit() else 0
            return 0

        h_tiri, a_tiri = get_s(0, 'Shots on Goal'), get_s(1, 'Shots on Goal')
        h_att, a_att = get_s(0, 'Dangerous Attacks'), get_s(1, 'Dangerous Attacks')

        if h_tiri >= a_tiri + 3 and h_att > a_att * 1.5: return {"side": "HOME", "name": "CASA"}
        if a_tiri >= h_tiri + 3 and a_att > h_att * 1.5: return {"side": "AWAY", "name": "TRASFERTA"}
        return None
    except: return None

def run_bot():
    print("🚀 Avvio sistema ELITE...")
    dati = carica_dati()
    active_bet = None
    
    # Primo tentativo di contatto
    if send_tg(f"🤖 **SISTEMA ELITE ONLINE**\n💰 Bankroll: {dati['bankroll']}€"):
        print("✅ Telegram collegato!")
    else:
        print("❌ Fallimento Telegram. Controlla il Token su Railway.")

    while True:
        try:
            dati = carica_dati()
            
            if active_bet:
                r = requests.get(f"https://api-sports.io{active_bet['id']}", headers={"x-apisports-key": API_KEY_FOOTBALL}, timeout=10)
                res_list = r.json().get('response', [])
                if res_list:
                    res = res_list[0]
                    if res['fixture']['status']['short'] in ['FT', 'AET', 'PEN']:
                        g_h, g_a = res['goals']['home'], res['goals']['away']
                        win = (active_bet['side'] == "HOME" and g_h > g_a) or (active_bet['side'] == "AWAY" and g_a > g_h)
                        profit = round(active_bet['stake'] * 0.45, 2) if win else -active_bet['stake']
                        dati['bankroll'] = round(dati['bankroll'] + profit, 2)
                        send_tg(f"{'✅ WIN' if win else '❌ LOSS'}\n💰 Profitto: {profit}€\n🏦 Bank: {dati['bankroll']}€")
                        active_bet = None
                        salva_dati(dati)
            else:
                r = requests.get("https://api-sports.io", headers={"x-apisports-key": API_KEY_FOOTBALL}, timeout=10)
                live_data = r.json().get('response', [])
                for p in live_data:
                    tempo = p['fixture']['status']['elapsed'] or 0
                    if 25 <= tempo <= 75:
                        analisi = analizza_dominio_reale(p['fixture']['id'])
                        if analisi:
                            stake = round(dati['bankroll'] * 0.10, 2) if dati['bankroll'] < 500 else round(dati['bankroll'] * 0.05, 2)
                            active_bet = {"id": p['fixture']['id'], "side": analisi['side'], "stake": stake, "odd": 1.45}
                            send_tg(f"🔥 **SEGNALE**\n⚽ {p['teams']['home']['name']} - {p['teams']['away']['name']}\n🎯 Puntata: {analisi['name']}\n💰 Stake: {stake}€")
                            break

            time.sleep(300)
        except Exception as e:
            print(f"⚠️ Errore loop: {e}")
            time.sleep(60)

if __name__ == "__main__":
    run_bot()
