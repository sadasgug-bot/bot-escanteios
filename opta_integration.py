import requests
import time
from datetime import datetime

class OptaStats:
    def __init__(self, api_football):
        self.api_football = api_football
        # Usaremos a API Football como base e enriqueceremos com dados Opta
    
    def get_enhanced_match_stats(self, fixture_id):
        """
        Enriquece as estatísticas da API Football com métricas estilo Opta
        """
        try:
            # Busca estatísticas básicas da API Football
            statistics = self.api_football.get_fixture_statistics(fixture_id)
            events = self.api_football.get_fixture_events(fixture_id)
            
            if not statistics:
                return None
            
            enhanced_stats = {
                'basic_stats': statistics,
                'opta_metrics': self.calculate_opta_metrics(statistics, events),
                'corner_analysis': self.analyze_corner_patterns(events),
                'pressure_index': self.calculate_pressure_index(statistics, events)
            }
            
            return enhanced_stats
            
        except Exception as e:
            print(f"❌ Erro Opta: {e}")
            return None
    
    def calculate_opta_metrics(self, statistics, events):
        """
        Calcula métricas avançadas no estilo Opta
        """
        try:
            metrics = {
                'attack_momentum': 0,
                'set_piece_danger': 0,
                'final_third_pressure': 0,
                'expected_goals_quality': 0
            }
            
            # Análise de eventos para calcular momentum
            shots_on_target = 0
            dangerous_attacks = 0
            successful_dribbles = 0
            
            for event in events:
                event_type = event.get('type')
                detail = event.get('detail', '')
                
                # Finalizações no gol
                if event_type == 'Shot' and 'on target' in detail.lower():
                    shots_on_target += 1
                
                # Ataques perigosos (finalizações de dentro da área)
                if event_type == 'Shot' and 'box' in detail.lower():
                    dangerous_attacks += 1
                
                # Dribles bem-sucedidos
                if event_type == 'Dribble' and 'successful' in detail.lower():
                    successful_dribbles += 1
            
            # Cálculo do momentum de ataque
            metrics['attack_momentum'] = min(100, (shots_on_target * 15) + (dangerous_attacks * 10) + (successful_dribbles * 5))
            
            # Perigo de bolas paradas (baseado em escanteios e faltas)
            corners = len([e for e in events if e.get('type') == 'Corner'])
            free_kicks = len([e for e in events if e.get('type') == 'Free Kick'])
            metrics['set_piece_danger'] = min(100, (corners * 8) + (free_kicks * 5))
            
            return metrics
            
        except Exception as e:
            print(f"❌ Erro cálculo Opta: {e}")
            return {}
    
    def analyze_corner_patterns(self, events):
        """
        Analisa padrões específicos de escanteios
        """
        try:
            corners = [e for e in events if e.get('type') == 'Corner']
            
            analysis = {
                'total_corners': len(corners),
                'corners_first_half': len([c for c in corners if c.get('time', {}).get('elapsed', 0) <= 45]),
                'corners_second_half': len([c for c in corners if c.get('time', {}).get('elapsed', 0) > 45]),
                'corner_frequency': 0,
                'recent_corner_momentum': 0
            }
            
            # Frequência de escanteios (por minuto)
            if corners:
                last_corner_time = max([c.get('time', {}).get('elapsed', 0) for c in corners])
                analysis['corner_frequency'] = len(corners) / max(1, last_corner_time) * 90
            
            # Momentum recente (escanteios nos últimos 15 minutos)
            recent_corners = len([c for c in corners if c.get('time', {}).get('elapsed', 0) >= (90 - 15)])
            analysis['recent_corner_momentum'] = recent_corners
            
            return analysis
            
        except Exception as e:
            print(f"❌ Erro análise escanteios: {e}")
            return {}
    
    def calculate_pressure_index(self, statistics, events):
        """
        Calcula índice de pressão no estilo Opta
        """
        try:
            pressure_index = 0
            
            # Baseado em posse de bola, finalizações e escanteios
            for team_stats in statistics:
                stats = team_stats.get('statistics', [])
                
                # Posse de bola
                possession = next((s for s in stats if s.get('type') == 'Ball Possession'), {})
                possession_value = possession.get('value', 0)
                if isinstance(possession_value, str) and '%' in possession_value:
                    possession_value = float(possession_value.replace('%', ''))
                
                # Finalizações totais
                total_shots = next((s for s in stats if s.get('type') == 'Total Shots'), {})
                shots_value = total_shots.get('value', 0)
                
                # Ataques perigosos
                attacks = next((s for s in stats if s.get('type') in ['Attacks', 'Dangerous Attacks']), {})
                attacks_value = attacks.get('value', 0)
                
                # Contribuição para o índice de pressão
                team_pressure = (possession_value * 0.3) + (shots_value * 20) + (attacks_value * 0.5)
                pressure_index += team_pressure
            
            return min(100, pressure_index / 2)
            
        except Exception as e:
            print(f"❌ Erro cálculo pressão: {e}")
            return 0
    
    def get_corner_prediction_score(self, enhanced_stats):
        """
        Calcula score de previsão de escanteios baseado em dados Opta
        """
        try:
            if not enhanced_stats:
                return 0
            
            opta_metrics = enhanced_stats.get('opta_metrics', {})
            corner_analysis = enhanced_stats.get('corner_analysis', {})
            pressure_index = enhanced_stats.get('pressure_index', 0)
            
            # Fatores que influenciam escanteios
            attack_momentum = opta_metrics.get('attack_momentum', 0)
            set_piece_danger = opta_metrics.get('set_piece_danger', 0)
            corner_frequency = corner_analysis.get('corner_frequency', 0)
            recent_momentum = corner_analysis.get('recent_corner_momentum', 0)
            
            # Cálculo do score (0-100)
            score = (
                (attack_momentum * 0.3) +
                (set_piece_danger * 0.25) + 
                (corner_frequency * 2) +
                (recent_momentum * 10) +
                (pressure_index * 0.15)
            )
            
            return min(100, max(0, score))
            
        except Exception as e:
            print(f"❌ Erro predição escanteios: {e}")
            return 0
