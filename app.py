def analyze_match_ht(match):
    """Analisa condições para HT"""
    fixture_id = match['fixture']['id']
    
    # Verifica se já foi notificado
    if fixture_id in notified_matches_ht:
        return None
    
    # ✅ CORREÇÃO: Use os métodos corretos da API
    statistics = football_api.get_fixture_statistics(fixture_id)
    events = football_api.get_fixture_events(fixture_id)
    odds = football_api.get_odds(fixture_id)
    
    # Conta escanteios no 1º tempo
    corners_ht = 0
    for event in events:
        if (event.get('type') == 'Corner' and 
            event.get('time', {}).get('elapsed', 0) <= 45):
            corners_ht += 1
    
    # Resto do código mantém igual...
    home_team = match['teams']['home']['name']
    away_team = match['teams']['away']['name']
    
    conditions_met = 0
    conditions_detail = []
    
    # Condição 1: + de 3 escanteios no 1º tempo
    if corners_ht > 3:
        conditions_met += 1
        conditions_detail.append(f"✅ {corners_ht} escanteios no 1T")
    else:
        conditions_detail.append(f"❌ {corners_ht} escanteios no 1T")
    
    # Condição 2: Odd > 1.25 para +0.5 escanteio HT
    corner_odds = get_corner_odds(odds)
    if corner_odds and corner_odds > 1.25:
        conditions_met += 1
        conditions_detail.append(f"✅ Odd +0.5: {corner_odds}")
    else:
        odds_display = corner_odds if corner_odds else "N/A"
        conditions_detail.append(f"❌ Odd +0.5: {odds_display}")
    
    # Condição 3: Time favorito pressionando
    if is_favorite_pressing(match, statistics):
        conditions_met += 1
        conditions_detail.append("✅ Favorito pressionando")
    else:
        conditions_detail.append("❌ Favorito pressionando")
    
    # Condição 4: XG de algum time > 0.50
    home_xg = get_team_xg(statistics, home_team)
    away_xg = get_team_xg(statistics, away_team)
    max_xg = max(home_xg, away_xg)
    
    if max_xg > 0.50:
        conditions_met += 1
        conditions_detail.append(f"✅ XG: {max_xg:.2f}")
    else:
        conditions_detail.append(f"❌ XG: {max_xg:.2f}")
    
    # Retorna análise se atender pelo menos 1 condição
    if conditions_met >= 1:
        notified_matches_ht.add(fixture_id)
        return {
            'fixture_id': fixture_id,
            'match_name': f"{home_team} vs {away_team}",
            'corners_ht': corners_ht,
            'conditions_met': conditions_met,
            'conditions_detail': conditions_detail,
            'score': match['goals'],
            'status': 'HT',
            'minute': match['fixture']['status']['elapsed'],
            'home_xg': home_xg,
            'away_xg': away_xg,
            'corner_odds': corner_odds
        }
    
    return None
