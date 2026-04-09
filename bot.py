def scansiona_mondo():
    # 🌍 LISTA COMPLETA CAMPIONATI (Major + Minor + Global)
    categorie = [
        # Top Leagues & Coppe
        "soccer_epl", "soccer_italy_serie_a", "soccer_spain_la_liga", 
        "soccer_germany_bundesliga", "soccer_france_ligue_1", 
        "soccer_uefa_champs_league", "soccer_uefa_europa_league",
        
        # Secondi Livelli & Altri Europei
        "soccer_italy_serie_b", "soccer_spain_segunda_division", 
        "soccer_germany_bundesliga2", "soccer_france_ligue_2",
        "soccer_portugal_primeira_liga", "soccer_netherlands_eredivisie",
        "soccer_belgium_first_division", "soccer_turkey_super_league",
        "soccer_austria_bundesliga", "soccer_denmark_superliga",
        
        # Americhe & Resto del Mondo (Minor/Global)
        "soccer_brazil_campeonato", "soccer_mexico_mx", 
        "soccer_usa_mls", "soccer_argentina_primera_division",
        "soccer_australia_aleague", "soccer_china_superleague",
        "soccer_japan_j_league", "soccer_korea_kl1"
    ]
    
    totale_segnali = 0
    log(f"🔄 Inizio scansione di {len(categorie)} competizioni...")
    
    for lega in categorie:
        # log(f"📡 Scansione: {lega}...") # Opzionale: decommenta se vuoi vedere ogni singola lega nei log
        num_trovati = analizza_lega(lega)
        totale_segnali += num_trovati
        
        # 🛡️ PROTEZIONE: Pausa di 1.5 secondi tra ogni lega 
        # Questo impedisce a Railway di andare in "OOM" (Out of Memory)
        time.sleep(1.5) 
    
    log(f"✅ CICLO COMPLETATO. Segnali totali inviati: {totale_segnali}")

# --- RESTO DEL CODICE INVARIATO (Loop a 1 ora) ---
