import requests
import time
import datetime
import pytz
import os

# ==========================================
# ⚙️ CONFIGURAZIONE (INSERISCI I TUOI DATI)
# ==========================================
API_FOOTBALL_KEY = "LA_TUA_API_FOOTBALL_KEY" # Da ://api-football.com
TELEGRAM_TOKEN = "IL_TUO_TELEGRAM_TOKEN"
CHAT_ID = "IL_TUO_CHAT_ID"

# ==========================================
# 🧠 CORE ENGINE: ELITE SYSTEM V3
# ==========================================
class EliteBot:
    def __init__(self):
        self.bankroll = 50.0  # Partenza piano 50€
        self.daily_loss = 0.0
        self.stop_loss_limit = 0.15 # 15% Stop-loss
        self.active_bet = None
        self.last_update_id = 0
        self.tz = pytz.timezone("Europe/Rome")

    def send_msg(self, text):
        url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})

    # --- ANALISI STATISTICHE LIVE ---
    def fetch_live_signals(self):
        url = "https://api-sports.io"
        headers = {'x-rapidapi-key': API_FOOTBALL_KEY}
        
        try:
            res = requests.get(url, headers=headers).json()
            for f in res.get('response', []):
                # Estrazione stats
                stats = f.get('statistics', [])
                if len(stats) < 2: continue
                
                h_shots = self._get_stat(stats[0], 'Shots on Goal')
                a_shots = self._get_stat(stats[1], 'Shots on Goal')
                h_name = f['teams']['home']['name']
                a_name = f['teams']['away']['name']
                score = f['goals']

                # FILTRO ELITE: Dominio netto ma pareggio/svantaggio
                if h_shots >= 5 and score['home'] <= score['away']:
                    return {"match": f"{h_name} vs {a_name}", "pick": h_name, "reason": f"🔥 DOMINIO: {h_shots} tiri in porta"}
                if a_shots >= 5 and score['away'] <= score['home']:
                    return {"match": f"{h_name} vs {a_name}", "pick": a_name, "reason": f"🔥 DOMINIO: {a_shots} tiri in porta"}
        except Exception as e:
            print(f"Errore API: {e}")
        return None

    def _get_stat(self, team_stats, stat_name):
        for s in team_stats['statistics']:
            if s['type'] == stat_name: return int(s['value'] or 0)
        return 0

    # --- GESTIONE MONEY MANAGEMENT ---
    def get_stake(self):
        # Piano di crescita accelerato
        if self.bankroll < 200: return round(self.bankroll * 0.10, 2) # 10% per scalare
        if self.bankroll < 1000: return round(self.bankroll * 0.07, 2) # 7% consolidamento
        return round(self.bankroll * 0.05, 2) # 5% regime (target 150€/giorno)

    def handle_tg(self):
        url = f"https://telegram.org{TELEGRAM_TOKEN}/getUpdates?offset={self.last_update_id + 1}"
        try:
            updates = requests.get(url).json().get("result", [])
            for u in updates:
                self.last_update_id = u["update_id"]
                msg = u.get("message", {}).get("text", "").upper()
                
                if msg == "STATUS":
                    progresso = (self.bankroll / 2500) * 100
                    self.send_msg(f"📊 *REPORT LIVE*\n💰 Bank: {round(self.bankroll,2)}€\n📉 Loss Oggi: {round(self.daily_loss,2)}€\n🚀 Target: {min(100, round(progresso,1))}% verso 150€/die")
                
                elif msg == "WIN" and self.active_bet:
                    profit = round(self.active_bet['stake'] * (self.active_bet['quota'] - 1), 2)
                    self.bankroll += profit
                    self.send_msg(f"✅ *CASSA!* +{profit}€\n🏦 Bankroll: {round(self.bankroll,2)}€")
                    self.active_bet = None
                    
                elif msg == "LOSS" and self.active_bet:
                    loss = self.active_bet['stake']
                    self.bankroll -= loss
                    self.daily_loss += loss
                    self.send_msg(f"❌ *PERSA* -{loss}€\n🏦 Bankroll: {round(self.bankroll,2)}€")
                    self.active_bet = None
        except: pass

# ==========================================
# 🚀 MAIN LOOP
# ==========================================
bot = EliteBot()
bot.send_msg("🚀 *SISTEMA ELITE V3 ATTIVO*\nTarget: 50€ ➔ 150€/giorno\nComandi: STATUS, WIN, LOSS")

while True:
    bot.handle_tg()

    # Controllo Stop-Loss Giornaliero
    if bot.daily_loss >= (bot.bankroll * bot.stop_loss_limit):
        bot.send_msg("⚠️ *STOP-LOSS RAGGIUNTO* per oggi. Il bot si ferma per sicurezza.")
        time.sleep(3600 * 12) # Pausa 12 ore
        bot.daily_loss = 0
        continue

    # Ricerca Bet se non ce n'è una attiva
    if bot.active_bet is None:
        segnalazione = bot.fetch_live_signals()
        if segnalazione:
            # Qui si assume una quota media live di 1.60 per il calcolo, 
            # l'utente la verificherà sul bookmaker
            stake = bot.get_stake()
            bot.active_bet = {"match": segnalazione['match'], "stake": stake, "quota": 1.60}
            
            msg = (f"🎯 *NUOVO SEGNALE VALORE*\n\n"
                   f"⚽ {segnalazione['match']}\n"
                   f"💡 Puntata su: *{segnalazione['pick']}*\n"
                   f"📊 Info: {segnalazione['reason']}\n"
                   f"💰 Stake consigliato: *{stake}€*\n\n"
                   f"Rispondi WIN o LOSS")
            bot.send_msg(msg)

    time.sleep(60) # Scan ogni minuto
