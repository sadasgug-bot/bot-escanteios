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
    
    def get_live_matches(self):
        """Busca todos os jogos ao vivo"""
        url = f"{self.base_url}/fixtures"
        params = {
            'live': 'all'
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get('response', [])
            else:
                print(f"Erro na API: {response.status_code}")
                return []
        except Exception as e:
            print(f"Erro ao buscar jogos ao vivo: {e}")
            return []
    
    def get_match_statistics(self, fixture_id):
        """Busca estatísticas detalhadas de uma partida"""
        url = f"{self.base_url}/fixtures/statistics"
        params = {
            'fixture': fixture_id
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get('response', [])
            return []
        except Exception as e:
            print(f"Erro ao buscar estatísticas: {e}")
            return []
    
    def get_match_events(self, fixture_id):
        """Busca eventos da partida (incluindo escanteios)"""
        url = f"{self.base_url}/fixtures/events"
        params = {
            'fixture': fixture_id
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get('response', [])
            return []
        except Exception as e:
            print(f"Erro ao buscar eventos: {e}")
            return []
    
    def get_match_odds(self, fixture_id):
        """Busca odds para escanteios"""
        url = f"{self.base_url}/odds"
        params = {
            'fixture': fixture_id,
            'bookmaker': 1,  # Bet365
            'bet': 1  # Corners
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get('response', [])
            return []
        except Exception as e:
            print(f"Erro ao buscar odds: {e}")
            return []
