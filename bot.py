import requests
import time
import datetime
import pytz
import os
import sys

# ==========================================
# ⚙️ CONFIGURAZIONE SICURA (VARIABILI D'AMBIENTE)
# ==========================================
API_FOOTBALL_KEY = os.environ.get("API_FOOTBALL_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# Controllo iniziale chiavi
if not all([API_FOOTBALL_KEY, TELEGRAM_TOKEN, CHAT_ID]):
    print("❌ ERRORE: Variabili d'ambiente mancanti su Railway!")
    sys.exit(1)

class EliteBot:
    def __init__(self):
        self.bankroll = 50.0
        self.daily_loss = 0.0
        self.stop_loss_limit = 0.15 
        self.active_bet = None
        self.last_update_id = 0
        self.tz = pytz.timezone("Europe/Rome")

    def send_msg(self, text):
        url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
        try:
            requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=10)
        except Exception as e:
            print(f"Errore invio Telegram: {e}")

    def fetch_live_signals(self):
        print(f"[{datetime.datetime.now(self.tz)}] 🔍 Scansione partite live...")
        url = "https://api-sports.io"
        headers = {'x-rapidapi-key': API_FOOTBALL_KEY}
        
        try:
            res = requests.get(url, headers=headers, timeout=15).json()
            if 'response' not in res: return None
            
            for f in res['response']:
                stats = f.get('statistics', [])
                if len(stats) < 2: continue
                
                h_shots = self._get_stat(stats, 0, 'Shots on Goal')
                a_shots = self._get_stat(stats, 1, 'Shots on Goal')
                score = f['goals']

                # LOGICA ELITE: Squadra in pressione che non sta vincendo
                if h_shots >= 5 and score['home'] <= score['away']:
                    return {"match": f"{f['teams']['home']['name']} vs {f['teams']['away']['name']}", "pick": f['teams']['home']['name'], "reason": f"🔥 {h_shots} tiri in porta"}
                if a_shots >= 5 and score['away'] <= score['home']:
                    return {"match": f"{f['teams']['home']['name']} vs {f['teams']['away']['name']}", "pick": f['teams']['away']['name'], "reason": f"🔥 {a_shots} tiri in porta"}
        except Exception as e:
            print(f"Errore fetch API: {e}")
        return None

    def _get_stat(self, stats, team_idx, stat_name):
        try:
            for s in stats[team_idx]['statistics']:
                if s['type'] == stat_name: return int(s['value'] or 0)
        except: return 0
        return 0

    def get_stake(self):
        if self.bankroll < 200: return round(self.bankroll * 0.10, 2)
        return round(self.bankroll * 0.05, 2)

    def handle_tg(self):
        url = f"https://telegram.org{TELEGRAM_TOKEN}/getUpdates?offset={self.last_update_id + 1}"
        try:
            res = requests.get(url, timeout=10).json()
            for u in res.get("result", []):
                self.last_update_id = u["update_id"]
                msg = u.get("message", {}).get("text", "").upper()
                
                if msg == "STATUS":
                    progresso = (self.bankroll / 2500) * 100
                    self.send_msg(f"📊 *STATO*\n💰 Bank: {round(self.bankroll,2)}€\n🚀 Target Elite: {round(progresso,1)}%")
                elif msg == "WIN" and self.active_bet:
                    profit = round(self.active_bet['stake'] * 0.60, 2) # Assumendo quota media 1.60
                    self.bankroll += profit
                    self.send_msg(f"✅ CASSA! +{profit}€")
                    self.active_bet = None
                elif msg == "LOSS" and self.active_bet:
                    self.bankroll -= self.active_bet['stake']
                    self.daily_loss += self.active_bet['stake']
                    self.send_msg(f"❌ PERSA. Bank: {round(self.bankroll,2)}€")
                    self.active_bet = None
        except: pass

# --- START ---
bot = EliteBot()
print("🚀 Bot Avviato correttamente!")
bot.send_msg("🚀 *SISTEMA ELITE ONLINE*\nPronto per la scalata da 50€!")

while True:
    try:
        bot.handle_tg()
        if bot.active_bet is None:
            sig = bot.fetch_live_signals()
            if sig:
                stake = bot.get_stake()
                bot.active_bet = {"match": sig['match'], "stake": stake}
                bot.send_msg(f"🎯 *BET RILEVATA*\n⚽ {sig['match']}\n💡 Punta su: {sig['pick']}\n📊 Info: {sig['reason']}\n💰 Stake: {stake}€")
        
        time.sleep(60)
    except Exception as e:
        print(f"Errore nel loop principale: {e}")
        time.sleep(30)
