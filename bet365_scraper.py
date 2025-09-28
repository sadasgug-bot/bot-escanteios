import requests
from bs4 import BeautifulSoup
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class Bet365Scraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def get_corner_odds_selenium(self, home_team, away_team):
        """
        Busca odds de escanteios usando Selenium para sites complexos como Bet365
        """
        try:
            # Configuração do Chrome headless
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            
            driver = webdriver.Chrome(options=chrome_options)
            
            try:
                # Acessa um site de odds agregador (mais fácil que Bet365 direto)
                url = f"https://www.oddsportal.com/search/?q={home_team}+{away_team}"
                driver.get(url)
                
                # Aguarda carregamento
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "flex"))
                )
                
                # Procura por odds de escanteios
                page_source = driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                
                # Procura por "Corners" ou "Escanteios" na página
                corners_odds = self.extract_corners_odds_from_html(str(page_source))
                
                return corners_odds
                
            except Exception as e:
                print(f"Erro Selenium: {e}")
                return self.get_corner_odds_fallback(home_team, away_team)
            finally:
                driver.quit()
                
        except Exception as e:
            print(f"Erro geral Selenium: {e}")
            return self.get_corner_odds_fallback(home_team, away_team)
    
    def get_corner_odds_fallback(self, home_team, away_team):
        """
        Método fallback usando API de odds alternativa
        """
        try:
            # Usa The Odds API como fallback
            api_key = "YOUR_THE_ODDS_API_KEY"  # Você pode conseguir em the-odds-api.com
            url = f"https://api.the-odds-api.com/v4/sports/soccer_brazil_campeonato/odds"
            params = {
                'apiKey': api_key,
                'regions': 'eu',
                'markets': 'corners',
                'oddsFormat': 'decimal'
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return self.extract_corners_from_odds_api(data, home_team, away_team)
            
            return None
        except:
            return self.calculate_estimated_odds(home_team, away_team)
    
    def extract_corners_odds_from_html(self, html_content):
        """
        Extrai odds de escanteios do HTML
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Procura por padrões de odds de escanteios
            patterns = [
                r'corners?.*?(\d+\.\d+)',  # corners 1.85
                r'escanteios?.*?(\d+\.\d+)',  # escanteios 1.90
                r'over.*?(\d+\.\d+).*?corners?',  # over 2.5 corners
                r'\+0\.5.*?(\d+\.\d+)',  # +0.5 1.25
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, html_content.lower())
                if matches:
                    return float(matches[0])
            
            return None
        except:
            return None
    
    def calculate_estimated_odds(self, home_team, away_team):
        """
        Calcula odds estimadas baseadas em estatísticas dos times
        """
        try:
            # Aqui você pode implementar lógica baseada em:
            # - Média histórica de escanteios
            # - Força dos times
            # - Importância da partida
            
            # Por enquanto, retorna um valor padrão baseado em estatísticas gerais
            base_odds = 1.30
            
            # Ajusta baseado no "chute" do jogo
            # Jogos mais equilibrados tendem a ter mais escanteios
            if any(word in home_team.lower() for word in ['flamengo', 'palmeiras', 'corinthians', 'são paulo']):
                base_odds -= 0.05  # Times grandes pressionam mais
            
            if any(word in away_team.lower() for word in ['flamengo', 'palmeiras', 'corinthians', 'são paulo']):
                base_odds -= 0.05
            
            return max(1.10, min(1.60, base_odds))  # Limita entre 1.10 e 1.60
            
        except:
            return 1.35  # Fallback final
    
    def get_corner_odds_simple(self, home_team, away_team):
        """
        Método simplificado que simula odds realistas
        """
        try:
            # Lógica baseada em características dos times
            base_odds = 1.35
            
            # Times ofensivos → mais escanteios → odds mais baixas
            offensive_teams = ['flamengo', 'palmeiras', 'botafogo', 'gremio', 'atletico-mg']
            
            # Times defensivos → menos escanteios → odds mais altas
            defensive_teams = ['fortaleza', 'cuiaba', 'juventude', 'bahia']
            
            home_offensive = any(team in home_team.lower() for team in offensive_teams)
            away_offensive = any(team in away_team.lower() for team in offensive_teams)
            home_defensive = any(team in home_team.lower() for team in defensive_teams)
            away_defensive = any(team in away_team.lower() for team in defensive_teams)
            
            # Ajusta odds baseado no perfil
            if home_offensive or away_offensive:
                base_odds -= 0.08
            
            if home_defensive and away_defensive:
                base_odds += 0.10
            
            # Garante limites realistas
            return max(1.15, min(1.55, round(base_odds, 2)))
            
        except:
            return 1.35

# Instância global
bet365_scraper = Bet365Scraper()
