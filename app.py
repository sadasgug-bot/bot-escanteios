from flask import Flask, request, jsonify
from football_api import FootballAPI
from telegram_bot import TelegramBot
import schedule
import time
import threading
from datetime import datetime
import pytz

app = Flask(__name__)

# Configurações
FOOTBALL_API_KEY = "a41e060f1db0909fd4ff8d7fed3bc37e"
TELEGRAM_BOT_TOKEN = "8443274539:AAE-OZWtG_oqwOF3UEKNIS-UvcNsL1EC2ys"

# Inicializa APIs
football_api = FootballAPI(FOOTBALL_API_KEY)
telegram_bot = TelegramBot(TELEGRAM_BOT_TOKEN)

# Armazena jogos já notificados
notified_matches_ht = set()
notified_matches_ft = set()

def analyze_match_ht(match):
    """Analisa condições para HT"""
    fixture_id = match['fixture']['id']
    
    # Verifica se já foi notificado
    if fixture_id in notified_matches_ht:
        return None
    
    # Busca estatísticas e eventos
    statistics = football_api.get_match_statistics(fixture_id)
    events = football_api.get_match_events(fixture_id)
    odds = football_api.get_match_odds(fixture_id)
    
    # Conta escanteios no 1º tempo
    corners_ht = 0
    for event in events:
        if (event['type'] == 'Corner' and 
            event['time']['elapsed'] <= 45):
            corners_ht += 1
    
    # Verifica condições HT
    conditions_met = 0
    
    # Condição 1: + de 3 escanteios no 1º tempo
    if corners_ht > 3:
        conditions_met += 1
    
    # Condição 2: Odd > 1.25 para +0.5 escanteio HT
    # (Implementação simplificada - você precisará adaptar conforme a API de odds)
    corner_odds_ht = get_corner_odds_ht(odds)
    if corner_odds_ht and corner_odds_ht > 1.25:
        conditions_met += 1
    
    # Condição 3: Time favorito pressionando
    if is_favorite_pressing(match, statistics):
        conditions_met += 1
    
    # Condição 4: XG > 0.50
    if get_team_xg(statistics) > 0.50:
        conditions_met += 1
    
    # Retorna análise se atender pelo menos 1 condição
    if conditions_met >= 1:
        notified_matches_ht.add(fixture_id)
        return {
            'fixture_id': fixture_id,
            'match_name': f"{match['teams']['home']['name']} vs {match['teams']['away']['name']}",
            'corners_ht': corners_ht,
            'conditions_met': conditions_met,
            'score': match['goals'],
            'status': 'HT'
        }
    
    return None

def analyze_match_ft(match):
    """Analisa condições para FT"""
    fixture_id = match['fixture']['id']
    
    # Verifica se já foi notificado
    if fixture_id in notified_matches_ft:
        return None
    
    # Busca estatísticas e eventos
    statistics = football_api.get_match_statistics(fixture_id)
    events = football_api.get_match_events(fixture_id)
    odds = football_api.get_match_odds(fixture_id)
    
    # Conta escanteios no 1º tempo para FT também
    corners_ht = 0
    for event in events:
        if (event['type'] == 'Corner' and 
            event['time']['elapsed'] <= 45):
            corners_ht += 1
    
    # Verifica condições FT
    conditions_met = 0
    
    # Condição 1: + de 3 escanteios no 1º tempo
    if corners_ht > 3:
        conditions_met += 1
    
    # Condição 2: Odd > 1.25 para +0.5 escanteio FT
    corner_odds_ft = get_corner_odds_ft(odds)
    if corner_odds_ft and corner_odds_ft > 1.25:
        conditions_met += 1
    
    # Condição 3: Time favorito pressionando
    if is_favorite_pressing(match, statistics):
        conditions_met += 1
    
    # Condição 4: XG > 1.00
    if get_team_xg(statistics) > 1.00:
        conditions_met += 1
    
    # Retorna análise se atender pelo menos 1 condição
    if conditions_met >= 1:
        notified_matches_ft.add(fixture_id)
        return {
            'fixture_id': fixture_id,
            'match_name': f"{match['teams']['home']['name']} vs {match['teams']['away']['name']}",
            'corners_ht': corners_ht,
            'conditions_met': conditions_met,
            'score': match['goals'],
            'status': 'FT'
        }
    
    return None

def get_corner_odds_ht(odds):
    """Extrai odds para escanteios HT (implementação básica)"""
    # Você precisará adaptar conforme a estrutura da API de odds
    try:
        # Exemplo simplificado
        return 1.30  # Valor fixo para exemplo
    except:
        return None

def get_corner_odds_ft(odds):
    """Extrai odds para escanteios FT (implementação básica)"""
    try:
        return 1.30  # Valor fixo para exemplo
    except:
        return None

def is_favorite_pressing(match, statistics):
    """Verifica se time favorito está pressionando"""
    # Implementação básica - verifica se está perdendo ou empatando
    try:
        home_goals = match['goals']['home'] or 0
        away_goals = match['goals']['away'] or 0
        
        # Simplificação: considera o time da casa como favorito
        if home_goals <= away_goals:  # Perdendo ou empatando
            return True
        return False
    except:
        return False

def get_team_xg(statistics):
    """Extrai xG de algum time"""
    try:
        # Implementação básica - você precisará adaptar
        # conforme a estrutura real dos dados de xG
        for team_stats in statistics:
            for stat in team_stats.get('statistics', []):
                if stat.get('type') == 'expected_goals':
                    xg = float(stat.get('value', 0))
                    if xg > 0:
                        return xg
        return 0.6  # Valor padrão para exemplo
    except:
        return 0.6

def create_telegram_message(analysis):
    """Cria mensagem formatada para o Telegram"""
    if analysis['status'] == 'HT':
        return f"""
🔔 <b>ALERTA ESCANTEIOS - 1º TEMPO</b> 🔔

🏆 <b>Jogo:</b> {analysis['match_name']}
⚽ <b>Placar:</b> {analysis['score']['home']} - {analysis['score']['away']}
📊 <b>Escanteios 1T:</b> {analysis['corners_ht']}
✅ <b>Condições atendidas:</b> {analysis['conditions_met']}/4

💡 <b>Oportunidade identificada!</b>
        """
    else:
        return f"""
🔔 <b>ALERTA ESCANTEIOS - JOGO INTEIRO</b> 🔔

🏆 <b>Jogo:</b> {analysis['match_name']}
⚽ <b>Placar:</b> {analysis['score']['home']} - {analysis['score']['away']}
📊 <b>Escanteios 1T:</b> {analysis['corners_ht']}
✅ <b>Condições atendidas:</b> {analysis['conditions_met']}/4

💡 <b>Oportunidade identificada!</b>
        """

def scan_matches():
    """Escaneia todos os jogos ao vivo"""
    print(f"📡 Escaneando jogos ao vivo... {datetime.now()}")
    
    try:
        live_matches = football_api.get_live_matches()
        print(f"🎯 {len(live_matches)} jogos ao vivo encontrados")
        
        for match in live_matches:
            # Analisa para HT
            ht_analysis = analyze_match_ht(match)
            if ht_analysis:
                message = create_telegram_message(ht_analysis)
                telegram_bot.send_message(message)
                print(f"✅ Alerta HT enviado: {ht_analysis['match_name']}")
            
            # Analisa para FT
            ft_analysis = analyze_match_ft(match)
            if ft_analysis:
                message = create_telegram_message(ft_analysis)
                telegram_bot.send_message(message)
                print(f"✅ Alerta FT enviado: {ft_analysis['match_name']}")
                
    except Exception as e:
        print(f"❌ Erro no scan: {e}")

def schedule_scanner():
    """Executa o scanner periodicamente"""
    schedule.every(1).minutes.do(scan_matches)
    
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
        
        if text == '/start':
            telegram_bot.send_message(
                "🤖 Bot de Escanteios Ativo! ⚽\n\n"
                "Monitorando jogos ao vivo para oportunidades de escanteios...",
                chat_id
            )
        elif text == '/status':
            telegram_bot.send_message(
                "✅ Bot funcionando normalmente!\n"
                "📡 Monitorando todos os jogos ao vivo...",
                chat_id
            )
    
    return jsonify({'status': 'ok'})

@app.route('/manual_scan', methods=['GET'])
def manual_scan():
    """Endpoint para scan manual"""
    scan_matches()
    return jsonify({'status': 'scan completed'})

if __name__ == '__main__':
    # Inicia o scanner em thread separada
    scanner_thread = threading.Thread(target=schedule_scanner, daemon=True)
    scanner_thread.start()
    
    # Inicia o servidor Flask
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
