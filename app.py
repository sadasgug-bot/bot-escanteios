from flask import Flask, request, jsonify
from football_api import FootballAPI
from telegram_bot import TelegramBot
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

def get_corner_odds(odds_data):
    """Extrai odds de escanteios da Bet365"""
    try:
        if not odds_data:
            return None
            
        for odds in odds_data:
            bookmaker = odds.get('bookmakers', [{}])[0]
            if bookmaker.get('name') == 'Bet365':
                for bet in bookmaker.get('bets', []):
                    if bet.get('name') == 'Asian Handicap':
                        for value in bet.get('values', []):
                            if value.get('value') == '+0.5':
                                return float(value.get('odd', 0))
        return None
    except:
        return None

def is_favorite_pressing(match_data, statistics):
    """Verifica se time favorito está pressionando"""
    try:
        fixture = match_data.get('fixture', {})
        goals = match_data.get('goals', {})
        
        home_goals = goals.get('home', 0) or 0
        away_goals = goals.get('away', 0) or 0
        fixture_status = fixture.get('status', {}).get('short')
        
        # Se está no intervalo ou segundo tempo
        if fixture_status in ['HT', '2H']:
            # Time da casa está perdendo ou empatando
            if home_goals <= away_goals:
                return True
        
        return False
        
    except Exception as e:
        print(f"Erro ao verificar pressing: {e}")
        return False

def analyze_match_ht(match_data):
    """Analisa condições para HT"""
    fixture_id = match_data['fixture']['id']
    
    if fixture_id in notified_matches_ht:
        return None
    
    # Busca dados detalhados
    events = football_api.get_fixture_events(fixture_id)
    statistics = football_api.get_fixture_statistics(fixture_id)
    odds_data = football_api.get_odds(fixture_id)
    
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
    corner_odds = get_corner_odds(odds_data)
    if corner_odds and corner_odds > 1.25:
        conditions_met += 1
        conditions_detail.append(f"✅ Odd +0.5: {corner_odds}")
    else:
        odds_display = corner_odds if corner_odds else "N/A"
        conditions_detail.append(f"❌ Odd +0.5: {odds_display}")
    
    # Condição 3: Time favorito pressionando
    if is_favorite_pressing(match_data, statistics):
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
            'score': match_data['goals'],
            'status': 'HT',
            'minute': match_data['fixture']['status']['elapsed'],
            'home_xg': home_xg,
            'away_xg': away_xg,
            'corner_odds': corner_odds
        }
    
    return None

def analyze_match_ft(match_data):
    """Analisa condições para FT"""
    fixture_id = match_data['fixture']['id']
    
    if fixture_id in notified_matches_ft:
        return None
    
    # Busca dados detalhados
    events = football_api.get_fixture_events(fixture_id)
    statistics = football_api.get_fixture_statistics(fixture_id)
    odds_data = football_api.get_odds(fixture_id)
    
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
    corner_odds = get_corner_odds(odds_data)
    if corner_odds and corner_odds > 1.25:
        conditions_met += 1
        conditions_detail.append(f"✅ Odd +0.5: {corner_odds}")
    else:
        odds_display = corner_odds if corner_odds else "N/A"
        conditions_detail.append(f"❌ Odd +0.5: {odds_display}")
    
    # Condição 3: Time favorito pressionando
    if is_favorite_pressing(match_data, statistics):
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
    
    # Retorna análise se atender pelo menos 1 condição
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
            'corner_odds': corner_odds
        }
    
    return None

def create_telegram_message(analysis):
    """Cria mensagem formatada para o Telegram"""
    conditions_text = "\n".join(analysis['conditions_detail'])
    
    if analysis['status'] == 'HT':
        return f"""
🔔 <b>ALERTA ESCANTEIOS - 1º TEMPO</b> 🔔

🏆 <b>Jogo:</b> {analysis['match_name']}
⏰ <b>Minuto:</b> {analysis['minute']}'
⚽ <b>Placar:</b> {analysis['score']['home']} - {analysis['score']['away']}
📊 <b>Escanteios 1T:</b> {analysis['corners_ht']}

📈 <b>Condições:</b>
{conditions_text}

🎯 <b>Condições atendidas:</b> {analysis['conditions_met']}/4
💡 <b>Oportunidade identificada!</b>

#ESCANTEIOS #HT
        """
    else:
        return f"""
🔔 <b>ALERTA ESCANTEIOS - JOGO INTEIRO</b> 🔔

🏆 <b>Jogo:</b> {analysis['match_name']}
⏰ <b>Minuto:</b> {analysis['minute']}'
⚽ <b>Placar:</b> {analysis['score']['home']} - {analysis['score']['away']}
📊 <b>Escanteios 1T:</b> {analysis['corners_ht']}

📈 <b>Condições:</b>
{conditions_text}

🎯 <b>Condições atendidas:</b> {analysis['conditions_met']}/4
💡 <b>Oportunidade identificada!</b>

#ESCANTEIOS #FT
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
                alerts_sent += 1
            
            # Analisa para FT
            ft_analysis = analyze_match_ft(match)
            if ft_analysis:
                message = create_telegram_message(ft_analysis)
                if TELEGRAM_CHAT_ID:
                    telegram_bot.send_message(message)
                print(f"✅ Alerta FT enviado: {ft_analysis['match_name']}")
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
                "🤖 Bot de Escanteios Ativo! ⚽\n\n"
                "Monitorando jogos ao vivo para oportunidades de escanteios...\n\n"
                "Comandos:\n"
                "/start - Iniciar bot\n"
                "/status - Ver status\n"
                "/scan - Scan manual",
                chat_id
            )
        elif text == '/status':
            telegram_bot.send_message(
                "✅ Bot funcionando normalmente!\n"
                "📡 Monitorando todos os jogos ao vivo...\n"
                "⏰ Scan automático a cada 1 minuto",
                chat_id
            )
        elif text == '/scan':
            telegram_bot.send_message("🔄 Executando scan manual...", chat_id)
            scan_matches()
            telegram_bot.send_message("✅ Scan manual concluído!", chat_id)
    
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

if __name__ == '__main__':
    # Inicia o scanner em thread separada
    print("🚀 Iniciando Bot de Escanteios...")
    scanner_thread = threading.Thread(target=schedule_scanner, daemon=True)
    scanner_thread.start()
    
    # Inicia o servidor Flask
    port = int(os.environ.get('PORT', 10000))
    print(f"🌐 Servidor iniciando na porta {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
