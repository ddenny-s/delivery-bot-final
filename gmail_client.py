"""
Gmail API клиент с Service Account
"""
import base64
import os
import json
from google.oauth2 import service_account
from googleapiclient import discovery
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


class GmailClient:
    """Клиент для работы с Gmail API через Service Account"""
    
    def __init__(self, credentials_file: str = "credentials.json", token_file: str = "token.json"):
        """Инициализация Gmail клиента"""
        self.credentials_file = credentials_file
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Аутентификация в Gmail API через Service Account"""
        try:
            # Пытаемся загрузить Service Account ключ
            if os.path.exists(self.credentials_file):
                with open(self.credentials_file, 'r') as f:
                    service_account_info = json.load(f)
                
                credentials = service_account.Credentials.from_service_account_info(
                    service_account_info,
                    scopes=SCOPES
                )
                
                self.service = discovery.build('gmail', 'v1', credentials=credentials)
                logger.info("✅ Gmail клиент аутентифицирован через Service Account")
            else:
                logger.warning(f"⚠️ Файл {self.credentials_file} не найден")
                raise Exception(f"Credentials file {self.credentials_file} not found")
        except Exception as e:
            logger.error(f"❌ Ошибка при аутентификации: {e}")
            raise
    
    def get_emails_since(self, hours: int = 24) -> List[Dict]:
        """Получить письма за последние N часов"""
        try:
            if not self.service:
                logger.warning("⚠️ Gmail сервис не инициализирован")
                return []
            
            query = f'newer_than:{hours}h'
            results = self.service.users().messages().list(userId='me', q=query).execute()
            messages = results.get('messages', [])
            
            emails = []
            for message in messages:
                try:
                    msg = self.service.users().messages().get(userId='me', id=message['id']).execute()
                    emails.append(msg)
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка при получении письма {message['id']}: {e}")
            
            logger.info(f"📧 Получено {len(emails)} писем")
            return emails
        except Exception as e:
            logger.error(f"❌ Ошибка при получении писем: {e}")
            return []
    
    def get_email_body(self, message: Dict) -> str:
        """Извлечь текст из письма"""
        try:
            if 'parts' in message['payload']:
                parts = message['payload']['parts']
                data = parts[0]['body'].get('data', '')
            else:
                data = message['payload']['body'].get('data', '')
            
            if data:
                text = base64.urlsafe_b64decode(data).decode('utf-8')
                return text
            return ""
        except Exception as e:
            logger.error(f"❌ Ошибка при извлечении текста: {e}")
            return ""
    
    def get_email_subject(self, message: Dict) -> str:
        """Получить тему письма"""
        try:
            headers = message['payload']['headers']
            for header in headers:
                if header['name'] == 'Subject':
                    return header['value']
            return "No Subject"
        except Exception as e:
            logger.error(f"❌ Ошибка при получении темы: {e}")
            return "No Subject"
