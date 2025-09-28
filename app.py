from flask import Flask, request, jsonify
from football_api import FootballAPI
from telegram_bot import TelegramBot
from opta_integration import OptaStats
import schedule
import time
import threading
from datetime import datetime
import pytz
import os

app = Flask(__name__)

# Configurações
FOOTBALL_API_KEY = os.environ.get('FOOTBALL_API_KEY', 'a41e060f1db0909fd4ff8d7fed3bc37e')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '8443274539:AAE-OZWtG_oqwOF3UEKNIS-UvcNsL1EC2ys')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

# Inicializa APIs
football_api = FootballAPI(FOOTBALL_API_KEY)
telegram_bot = TelegramBot(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
opta_stats = OptaStats(football_api)  # ✅ OPTA INTEGRADO

# Armazena jogos já notificados
notified_matches_ht = set()
notified_matches_ft = set()

def get_corners_ht(events):
    """Conta escanteios no primeiro tempo"""
    corners = 0
    for event in events:
        if (event.get('type') == 'Corner' and 
            event.get('time', {}).get('elapsed', 0) <= 45):
            corners += 1
    return corners

def get_team_xg(statistics, team_name):
    """Extrai xG de um time específico"""
    try:
        for team_stats in statistics:
            if team_stats.get('team', {}).get('name') == team_name:
                for stat in team_stats.get('statistics', []):
                    if stat.get('type') == 'expected_goals':
                        xg_value = stat.get('value')
                        if xg_value is not None:
                            return float(xg_value) if xg_value else 0.0
        return 0.0
    except:
        return 0.0

def extract_corners_from_football_api(odds_data):
    """Tenta extrair odds de escanteios da API Football"""
    try:
        if not odds_data:
            return None
            
        for odds in odds_data:
            bookmakers = odds.get('bookmakers', [])
            for bookmaker in bookmakers:
                if bookmaker.get('name') == 'Bet365':
                    bets = bookmaker.get('bets', [])
                    for bet in bets:
                        if bet.get('name') in ['Corners', 'Escanteios', 'Asian Handicap']:
                            values = bet.get('values', [])
                            for value in values:
                                if value.get('value') == '+0.5':
                                    return float(value.get('odd', 0))
        return None
    except:
        return None

def calculate_estimated_odds(home_team, away_team):
    """
    Calcula odds estimadas baseadas em estatísticas dos times - SIMULA BET365
    """
    try:
        # Odds base mais realista
        base_odds = 1.32
        
        # Times ofensivos brasileiros → mais escanteios → odds mais baixas
        offensive_teams = [
            'flamengo', 'palmeiras', 'botafogo', 'grêmio', 'atlético-mg', 
            'são paulo', 'corinthians', 'internacional', 'fluminense', 'red bull',
            'fortaleza', 'athletico', 'cruzeiro', 'vasco', 'bahia', 'bragantino'
        ]
        
        # Times muito ofensivos → odds ainda mais baixas
        very_offensive_teams = ['flamengo', 'palmeiras', 'botafogo', 'grêmio', 'são paulo', 'bragantino']
        
        # Times defensivos → menos escanteios → odds mais altas
        defensive_teams = ['cuiabá', 'juventude', 'goiás', 'coritiba', 'américa-mg', 'atlético-go']
        
        home_lower = home_team.lower()
        away_lower = away_team.lower()
        
        # Ajusta baseado no perfil ofensivo
        home_offensive = any(team in home_lower for team in offensive_teams)
        away_offensive = any(team in away_lower for team in offensive_teams)
        home_very_offensive = any(team in home_lower for team in very_offensive_teams)
        away_very_offensive = any(team in away_lower for team in very_offensive_teams)
        home_defensive = any(team in home_lower for team in defensive_teams)
        away_defensive = any(team in away_lower for team in defensive_teams)
        
        # Lógica de ajuste de odds (MAIS CONSERVADORA)
        adjustments = 0.0
        
        if home_very_offensive and away_very_offensive:
            adjustments -= 0.10  # Jogo entre dois times ofensivos
        elif home_very_offensive or away_very_offensive:
            adjustments -= 0.06  # Pelo menos um time muito ofensivo
        elif home_offensive and away_offensive:
            adjustments -= 0.04  # Dois times ofensivos
        elif home_offensive or away_offensive:
            adjustments -= 0.02  # Pelo menos um time ofensivo
        
        # Times defensivos aumentam as odds
        if home_defensive and away_defensive:
            adjustments += 0.08  # Dois times defensivos
        elif home_defensive or away_defensive:
            adjustments += 0.04  # Pelo menos um time defensivo
        
        # Derbys e jogos importantes tendem a ter mais escanteios
        derby_keywords = ['fla-flu', 'flamengo-fluminense', 'cor-fra', 'corinthians-palmeiras', 
                         'gre-nal', 'grêmio-internacional', 'atlético-cruzeiro', 'clássico']
        
        match_name_lower = f"{home_lower}-{away_lower}".lower()
        if any(derby in match_name_lower for derby in derby_keywords):
            adjustments -= 0.03
        
        # Aplica ajustes
        final_odds = base_odds + adjustments
        
        # Garante limites realistas (entre 1.18 e 1.55)
        final_odds = max(1.18, min(1.55, round(final_odds, 2)))
        
        print(f"🎯 Odds calculadas para {home_team} vs {away_team}: {final_odds}")
        return final_odds
        
    except Exception as e:
        print(f"❌ Erro ao calcular odds: {e}")
        return 1.32  # Fallback

def get_corner_odds(match_data, odds_data=None):
    """Busca odds de escanteios - SIMULA BET365"""
    try:
        home_team = match_data['teams']['home']['name']
        away_team = match_data['teams']['away']['name']
        
        print(f"🔍 Buscando odds para: {home_team} vs {away_team}")
        
        # Tenta primeiro com a API Football (se disponível)
        if odds_data:
            traditional_odds = extract_corners_from_football_api(odds_data)
            if traditional_odds and traditional_odds > 1.10:
                print(f"✅ Odds da API Football: {traditional_odds}")
                return traditional_odds
        
        # Se não encontrou, usa cálculo inteligente baseado nos times
        calculated_odds = calculate_estimated_odds(home_team, away_team)
        print(f"✅ Odds calculadas (Bet365 simulado): {calculated_odds}")
        
        return calculated_odds
        
    except Exception as e:
        print(f"❌ Erro ao buscar odds: {e}")
        return 1.32  # Fallback

def is_favorite_pressing(match_data, statistics):
    """Verifica se time favorito está pressionando"""
    try:
        fixture = match_data.get('fixture', {})
        goals = match_data.get('goals', {})
        
        home_goals = goals.get('home', 0) or 0
        away_goals = goals.get('away', 0) or 0
        fixture_status = fixture.get('status', {}).get('short')
        minute = fixture.get('status', {}).get('elapsed', 0)
        
        # Considera o time da casa como favorito (simplificação)
        # Se está no primeiro tempo e perdendo/empatando
        if fixture_status == '1H' and minute >= 20:  # A partir do 20º minuto
            if home_goals <= away_goals:
                return True
        
        # Se está no intervalo
        elif fixture_status == 'HT':
            if home_goals <= away_goals:
                return True
                
        # Se está no segundo tempo
        elif fixture_status == '2H':
            if home_goals <= away_goals:
                return True
        
        return False
        
    except Exception as e:
        print(f"❌ Erro ao verificar pressing: {e}")
        return False

def analyze_match_ht(match_data):
    """Analisa condições para HT com dados Opta"""
    fixture_id = match_data['fixture']['id']
    
    if fixture_id in notified_matches_ht:
        return None
    
    # Busca dados detalhados + Opta
    events = football_api.get_fixture_events(fixture_id)
    statistics = football_api.get_fixture_statistics(fixture_id)
    odds_data = football_api.get_odds(fixture_id)
    enhanced_stats = opta_stats.get_enhanced_match_stats(fixture_id)  # ✅ OPTA
    
    corners_ht = get_corners_ht(events)
    home_team = match_data['teams']['home']['name']
    away_team = match_data['teams']['away']['name']
    
    conditions_met = 0
    conditions_detail = []
    
    # Condição 1: + de 3 escanteios no 1º tempo
    if corners_ht > 3:
        conditions_met += 1
        conditions_detail.append(f"✅ {corners_ht} escanteios no 1T")
    else:
        conditions_detail.append(f"❌ {corners_ht} escanteios no 1T")
    
    # Condição 2: Odd > 1.25 para +0.5 escanteio HT
    corner_odds = get_corner_odds(match_data, odds_data)
    if corner_odds and corner_odds > 1.25:
        conditions_met += 1
        conditions_detail.append(f"✅ Odd +0.5: {corner_odds}")
    else:
        odds_display = corner_odds if corner_odds else "N/A"
        conditions_detail.append(f"❌ Odd +0.5: {odds_display}")
    
    # Condição 3: Time favorito pressionando
    pressing = is_favorite_pressing(match_data, statistics)
    if pressing:
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
    
    # ✅ NOVA CONDIÇÃO 5: Score Opta > 50 (probabilidade de escanteios)
    opta_score = opta_stats.get_corner_prediction_score(enhanced_stats) if enhanced_stats else 0
    if opta_score > 50:
        conditions_met += 1
        conditions_detail.append(f"✅ Opta Score: {opta_score:.0f}")
    else:
        conditions_detail.append(f"❌ Opta Score: {opta_score:.0f}")
    
    # ✅ Agora precisa de apenas 1 condição
    if conditions_met >= 1:
        notified_matches_ht.add(fixture_id)
        return {
            'fixture_id': fixture_id,
            'match_name': f"{home_team} vs {away_team}",
            'corners_ht': corners_ht,
            'conditions_met': conditions_met,
            'conditions_detail': conditions_detail,
            'score': match_data['goals'],
            'status': 'HT',
            'minute': match_data['fixture']['status']['elapsed'],
            'home_xg': home_xg,
            'away_xg': away_xg,
            'corner_odds': corner_odds,
            'opta_score': opta_score,  # ✅ NOVO DADO
            'pressure_index': enhanced_stats.get('pressure_index', 0) if enhanced_stats else 0
        }
    
    return None

def analyze_match_ft(match_data):
    """Analisa condições para FT com dados Opta"""
    fixture_id = match_data['fixture']['id']
    
    if fixture_id in notified_matches_ft:
        return None
    
    # Busca dados detalhados + Opta
    events = football_api.get_fixture_events(fixture_id)
    statistics = football_api.get_fixture_statistics(fixture_id)
    odds_data = football_api.get_odds(fixture_id)
    enhanced_stats = opta_stats.get_enhanced_match_stats(fixture_id)  # ✅ OPTA
    
    corners_ht = get_corners_ht(events)
    home_team = match_data['teams']['home']['name']
    away_team = match_data['teams']['away']['name']
    
    conditions_met = 0
    conditions_detail = []
    
    # Condição 1: + de 3 escanteios no 1º tempo
    if corners_ht > 3:
        conditions_met += 1
        conditions_detail.append(f"✅ {corners_ht} escanteios no 1T")
    else:
        conditions_detail.append(f"❌ {corners_ht} escanteios no 1T")
    
    # Condição 2: Odd > 1.25 para +0.5 escanteio FT
    corner_odds = get_corner_odds(match_data, odds_data)
    if corner_odds and corner_odds > 1.25:
        conditions_met += 1
        conditions_detail.append(f"✅ Odd +0.5: {corner_odds}")
    else:
        odds_display = corner_odds if corner_odds else "N/A"
        conditions_detail.append(f"❌ Odd +0.5: {odds_display}")
    
    # Condição 3: Time favorito pressionando
    pressing = is_favorite_pressing(match_data, statistics)
    if pressing:
        conditions_met += 1
        conditions_detail.append("✅ Favorito pressionando")
    else:
        conditions_detail.append("❌ Favorito pressionando")
    
    # Condição 4: XG de algum time > 1.00
    home_xg = get_team_xg(statistics, home_team)
    away_xg = get_team_xg(statistics, away_team)
    max_xg = max(home_xg, away_xg)
    
    if max_xg > 1.00:
        conditions_met += 1
        conditions_detail.append(f"✅ XG: {max_xg:.2f}")
    else:
        conditions_detail.append(f"❌ XG: {max_xg:.2f}")
    
    # ✅ NOVA CONDIÇÃO 5: Score Opta > 50 (probabilidade de escanteios)
    opta_score = opta_stats.get_corner_prediction_score(enhanced_stats) if enhanced_stats else 0
    if opta_score > 50:
        conditions_met += 1
        conditions_detail.append(f"✅ Opta Score: {opta_score:.0f}")
    else:
        conditions_detail.append(f"❌ Opta Score: {opta_score:.0f}")
    
    # ✅ Agora precisa de apenas 1 condição
    if conditions_met >= 1:
        notified_matches_ft.add(fixture_id)
        return {
            'fixture_id': fixture_id,
            'match_name': f"{home_team} vs {away_team}",
            'corners_ht': corners_ht,
            'conditions_met': conditions_met,
            'conditions_detail': conditions_detail,
            'score': match_data['goals'],
            'status': 'FT',
            'minute': match_data['fixture']['status']['elapsed'],
            'home_xg': home_xg,
            'away_xg': away_xg,
            'corner_odds': corner_odds,
            'opta_score': opta_score,  # ✅ NOVO DADO
            'pressure_index': enhanced_stats.get('pressure_index', 0) if enhanced_stats else 0
        }
    
    return None

def create_telegram_message(analysis):
    """Cria mensagem formatada para o Telegram com dados Opta"""
    conditions_text = "\n".join(analysis['conditions_detail'])
    
    # Adiciona dados Opta se disponíveis
    opta_info = ""
    if analysis.get('opta_score'):
        opta_info = f"📊 <b>Opta Score:</b> {analysis['opta_score']:.0f}/100\n"
    
    if analysis['status'] == 'HT':
        return f"""
🔔 <b>ALERTA ESCANTEIOS - 1º TEMPO</b> 🔔

🏆 <b>Jogo:</b> {analysis['match_name']}
⏰ <b>Minuto:</b> {analysis['minute']}'
⚽ <b>Placar:</b> {analysis['score']['home']} - {analysis['score']['away']}
📊 <b>Escanteios 1T:</b> {analysis['corners_ht']}

{opta_info}
📈 <b>Condições:</b>
{conditions_text}

🎯 <b>Condições atendidas:</b> {analysis['conditions_met']}/5
💰 <b>Odd Bet365 (+0.5):</b> {analysis['corner_odds']}

💡 <b>Oportunidade identificada!</b>

#ESCANTEIOS #HT #OPTA
        """
    else:
        return f"""
🔔 <b>ALERTA ESCANTEIOS - JOGO INTEIRO</b> 🔔

🏆 <b>Jogo:</b> {analysis['match_name']}
⏰ <b>Minuto:</b> {analysis['minute']}'
⚽ <b>Placar:</b> {analysis['score']['home']} - {analysis['score']['away']}
📊 <b>Escanteios 1T:</b> {analysis['corners_ht']}

{opta_info}
📈 <b>Condições:</b>
{conditions_text}

🎯 <b>Condições atendidas:</b> {analysis['conditions_met']}/5
💰 <b>Odd Bet365 (+0.5):</b> {analysis['corner_odds']}

💡 <b>Oportunidade identificada!</b>

#ESCANTEIOS #FT #OPTA
        """

def scan_matches():
    """Escaneia todos os jogos ao vivo"""
    print(f"📡 Escaneando jogos ao vivo... {datetime.now()}")
    
    try:
        live_matches = football_api.get_live_matches()
        print(f"🎯 {len(live_matches)} jogos ao vivo encontrados")
        
        alerts_sent = 0
        
        for match in live_matches:
            # Analisa para HT
            ht_analysis = analyze_match_ht(match)
            if ht_analysis:
                message = create_telegram_message(ht_analysis)
                if TELEGRAM_CHAT_ID:
                    telegram_bot.send_message(message)
                    print(f"✅ Alerta HT enviado: {ht_analysis['match_name']}")
                else:
                    print(f"⚠️  Alerta HT (sem Chat ID): {ht_analysis['match_name']}")
                alerts_sent += 1
            
            # Analisa para FT
            ft_analysis = analyze_match_ft(match)
            if ft_analysis:
                message = create_telegram_message(ft_analysis)
                if TELEGRAM_CHAT_ID:
                    telegram_bot.send_message(message)
                    print(f"✅ Alerta FT enviado: {ft_analysis['match_name']}")
                else:
                    print(f"⚠️  Alerta FT (sem Chat ID): {ft_analysis['match_name']}")
                alerts_sent += 1
        
        print(f"📊 Scan concluído. {alerts_sent} alertas enviados")
                
    except Exception as e:
        print(f"❌ Erro no scan: {e}")

def schedule_scanner():
    """Executa o scanner periodicamente"""
    print("⏰ Agendador iniciado - Scan a cada 1 minuto")
    schedule.every(1).minutes.do(scan_matches)
    
    # Primeiro scan imediato
    print("🚀 Executando primeiro scan...")
    scan_matches()
    
    while True:
        schedule.run_pending()
        time.sleep(30)

@app.route('/')
def home():
    return "🤖 Bot de Escanteios Online! ⚽"

@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook para receber mensagens do Telegram"""
    update = request.get_json()
    
    if 'message' in update:
        chat_id = update['message']['chat']['id']
        text = update['message'].get('text', '')
        
        print(f"📱 Mensagem recebida: {text} de {chat_id}")
        
        if text == '/start':
            telegram_bot.send_message(
                "🤖 <b>Bot de Escanteios Ativo!</b> ⚽\n\n"
                "📡 <b>Monitorando jogos ao vivo</b>\n"
                "🎯 <b>Condições HT/FT para escanteios</b>\n"
                "💰 <b>Odds Bet365 simuladas</b>\n"
                "📊 <b>Estatísticas Opta integradas</b>\n\n"
                "<b>Comandos:</b>\n"
                "/start - Iniciar bot\n"
                "/status - Ver status\n"
                "/scan - Scan manual\n"
                "/info - Ver condições",
                chat_id
            )
        elif text == '/status':
            telegram_bot.send_message(
                "✅ <b>Bot funcionando normalmente!</b>\n"
                "📡 Monitorando todos os jogos ao vivo\n"
                "⏰ Scan automático a cada 1 minuto\n"
                "💰 Odds Bet365 simuladas\n"
                "📊 Estatísticas Opta ativas\n"
                "🎯 Alertas HT e FT",
                chat_id
            )
        elif text == '/scan':
            telegram_bot.send_message("🔄 Executando scan manual...", chat_id)
            scan_matches()
            telegram_bot.send_message("✅ Scan manual concluído!", chat_id)
        elif text == '/info':
            telegram_bot.send_message(
                "🎯 <b>CONDIÇÕES PARA ALERTAS:</b>\n\n"
                "<b>1º TEMPO (HT):</b>\n"
                "✅ +3 escanteios no 1T\n"
                "✅ Odd > 1.25 (+0.5)\n" 
                "✅ Favorito pressionando\n"
                "✅ xG > 0.50\n"
                "✅ Opta Score > 50\n\n"
                "<b>JOGO INTEIRO (FT):</b>\n"
                "✅ +3 escanteios no 1T\n"
                "✅ Odd > 1.25 (+0.5)\n"
                "✅ Favorito pressionando\n"
                "✅ xG > 1.00\n"
                "✅ Opta Score > 50\n\n"
                "<i>Precisa atender pelo menos 1 condição</i>",
                chat_id
            )
    
    return jsonify({'status': 'ok'})

@app.route('/manual_scan', methods=['GET'])
def manual_scan():
    """Endpoint para scan manual"""
    scan_matches()
    return jsonify({'status': 'scan completed'})

@app.route('/set_chat_id/<chat_id>', methods=['GET'])
def set_chat_id(chat_id):
    """Endpoint para definir Chat ID manualmente"""
    global TELEGRAM_CHAT_ID
    TELEGRAM_CHAT_ID = chat_id
    return jsonify({'status': 'chat_id set', 'chat_id': chat_id})

@app.route('/test_odds/<home_team>/<away_team>', methods=['GET'])
def test_odds(home_team, away_team):
    """Endpoint para testar cálculo de odds"""
    odds = calculate_estimated_odds(home_team, away_team)
    return jsonify({
        'home_team': home_team,
        'away_team': away_team, 
        'calculated_odds': odds
    })

@app.route('/debug_scan', methods=['GET'])
def debug_scan():
    """Endpoint de debug com informações detalhadas"""
    print(f"🔍 [DEBUG] Iniciando scan detalhado... {datetime.now()}")
    
    try:
        live_matches = football_api.get_live_matches()
        print(f"🔍 [DEBUG] {len(live_matches)} jogos ao vivo encontrados")
        
        if not live_matches:
            return jsonify({
                'status': 'no_live_matches',
                'message': 'Nenhum jogo ao vivo no momento'
            })
        
        debug_info = []
        
        for i, match in enumerate(live_matches[:3]):  # Analisa apenas os 3 primeiros
            fixture_id = match['fixture']['id']
            home_team = match['teams']['home']['name']
            away_team = match['teams']['away']['name']
            minute = match['fixture']['status']['elapsed']
            score = f"{match['goals']['home']}-{match['goals']['away']}"
            
            print(f"🔍 [DEBUG] Analisando: {home_team} vs {away_team} - {minute}' - {score}")
            
            # Busca dados básicos
            events = football_api.get_fixture_events(fixture_id)
            corners_ht = get_corners_ht(events)
            
            # Busca dados Opta
            enhanced_stats = opta_stats.get_enhanced_match_stats(fixture_id)
            opta_score = opta_stats.get_corner_prediction_score(enhanced_stats) if enhanced_stats else 0
            
            # Calcula odds
            odds = get_corner_odds(match, None)
            
            debug_info.append({
                'match': f"{home_team} vs {away_team}",
                'minute': minute,
                'score': score,
                'corners_ht': corners_ht,
                'odds': odds,
                'opta_score': opta_score,
                'fixture_id': fixture_id
            })
            
            print(f"🔍 [DEBUG] {home_team} vs {away_team}: {corners_ht} escanteios, Odd: {odds}, Opta: {opta_score}")
        
        return jsonify({
            'status': 'debug_completed',
            'total_matches': len(live_matches),
            'analyzed_matches': debug_info,
            'telegram_chat_id_configured': bool(TELEGRAM_CHAT_ID)
        })
        
    except Exception as e:
        print(f"❌ [DEBUG] Erro: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    # Inicia o scanner em thread separada
    print("🚀 Iniciando Bot de Escanteios...")
    print("💰 Sistema de odds Bet365 simulado ativo!")
    print("📊 Integração Opta Stats Perform ativa!")
    scanner_thread = threading.Thread(target=schedule_scanner, daemon=True)
    scanner_thread.start()
    
    # Inicia o servidor Flask
    port = int(os.environ.get('PORT', 10000))
    print(f"🌐 Servidor iniciando na porta {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
