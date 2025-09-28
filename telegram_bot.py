import requests
import json

class TelegramBot:
    def __init__(self, token, chat_id=None):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.chat_id = chat_id
    
    def send_message(self, text, chat_id=None):
        """Envia mensagem para o Telegram"""
        target_chat_id = chat_id or self.chat_id
        if not target_chat_id:
            print("Erro: Chat ID não especificado")
            return False
        
        url = f"{self.base_url}/sendMessage"
        payload = {
            'chat_id': target_chat_id,
            'text': text,
            'parse_mode': 'HTML'
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Erro ao enviar mensagem: {e}")
            return False
    
    def set_webhook(self, url):
        """Configura webhook para receber mensagens"""
        webhook_url = f"{url}/webhook"
        set_webhook_url = f"{self.base_url}/setWebhook?url={webhook_url}"
        
        try:
            response = requests.get(set_webhook_url, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Erro ao configurar webhook: {e}")
            return False

    def get_updates(self):
        """Busca atualizações do bot"""
        url = f"{self.base_url}/getUpdates"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Erro ao buscar updates: {e}")
            return None
