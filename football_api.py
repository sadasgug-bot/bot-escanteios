import requests
import time
from datetime import datetime, timedelta
import pytz

class FootballAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://v3.football.api-sports.io"
        self.headers = {
            'x-rapidapi-host': 'v3.football.api-sports.io',
            'x-rapidapi-key': self.api_key
        }
        self.request_count = 0
        self.last_reset = time.time()
    
    def make_request(self, endpoint, params=None):
        """Faz requisição com controle de rate limiting"""
        # Controle de rate limiting (100 requests/minuto)
        current_time = time.time()
        if current_time - self.last_reset >= 60:
            self.request_count = 0
            self.last_reset = current_time
        
        if self.request_count >= 95:  # Margem de segurança
            time.sleep(60 - (current_time - self.last_reset))
            self.request_count = 0
            self.last_reset = time.time()
        
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            self.request_count += 1
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                print("Rate limit atingido, aguardando 60 segundos...")
                time.sleep(60)
                return self.make_request(endpoint, params)
            else:
                print(f"Erro API {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            print(f"Erro na requisição: {e}")
            return None
    
    def get_live_matches(self):
        """Busca todos os jogos ao vivo"""
        data = self.make_request('fixtures', {'live': 'all'})
        if data and 'response' in data:
            return data['response']
        return []
    
    def get_fixture_details(self, fixture_id):
        """Busca detalhes completos de uma partida"""
        data = self.make_request('fixtures', {'id': fixture_id})
        if data and 'response' in data:
            return data['response'][0] if data['response'] else None
        return None
    
    def get_fixture_statistics(self, fixture_id):
        """Busca estatísticas da partida"""
        data = self.make_request('fixtures/statistics', {'fixture': fixture_id})
        if data and 'response' in data:
            return data['response']
        return []
    
    def get_fixture_events(self, fixture_id):
        """Busca eventos da partida (escanteios, gols, etc)"""
        data = self.make_request('fixtures/events', {'fixture': fixture_id})
        if data and 'response' in data:
            return data['response']
        return []
    
    def get_fixture_lineups(self, fixture_id):
        """Busca formações e dados dos times"""
        data = self.make_request('fixtures/lineups', {'fixture': fixture_id})
        if data and 'response' in data:
            return data['response']
        return []
    
    def get_odds(self, fixture_id):
        """Busca odds para a partida"""
        data = self.make_request('odds', {'fixture': fixture_id, 'bookmaker': 1})
        if data and 'response' in data:
            return data['response']
        return []
