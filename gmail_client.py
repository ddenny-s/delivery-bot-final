"""
Gmail API клиент
"""
import base64
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials as UserCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.exceptions import RefreshError
from googleapiclient import discovery
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


class GmailClient:
    """Клиент для работы с Gmail API"""
    
    def __init__(self, credentials_file: str = "credentials.json", token_file: str = "token.json"):
        """Инициализация Gmail клиента"""
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Аутентификация в Gmail API"""
        creds = None
        
        # Пытаемся загрузить существующий токен
        if os.path.exists(self.token_file):
            try:
                creds = UserCredentials.from_authorized_user_file(self.token_file, SCOPES)
                logger.info("✅ Токен загружен из файла")
            except Exception as e:
                logger.warning(f"⚠️ Не удалось загрузить токен: {e}")
        
        # Если токена нет или он невалиден
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    logger.info("✅ Токен обновлен")
                except RefreshError as e:
                    logger.warning(f"⚠️ Не удалось обновить токен: {e}")
                    raise Exception("Требуется переаутентификация")
            else:
                logger.warning("⚠️ Токен отсутствует или невалиден")
                raise Exception("Требуется переаутентификация через браузер")
        
        try:
            self.service = discovery.build('gmail', 'v1', credentials=creds)
            logger.info("✅ Gmail клиент аутентифицирован")
        except Exception as e:
            logger.error(f"❌ Ошибка при создании сервиса: {e}")
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
