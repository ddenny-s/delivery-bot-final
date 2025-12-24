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
        
        if os.path.exists(self.token_file):
            creds = UserCredentials.from_authorized_user_file(self.token_file, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except RefreshError:
                    logger.warning("Не удалось обновить токен, требуется переаутентификация")
                    self._get_new_credentials()
            else:
                self._get_new_credentials()
        
        self.service = discovery.build('gmail', 'v1', credentials=creds)
        logger.info("✅ Gmail клиент аутентифицирован")
    
    def _get_new_credentials(self):
        """Получить новые учетные данные"""
        flow = InstalledAppFlow.from_client_secrets_file(
            self.credentials_file, SCOPES)
        creds = flow.run_local_server(port=0)
        
        with open(self.token_file, 'w') as token:
            token.write(creds.to_json())
    
    def get_emails_since(self, hours: int = 24) -> List[Dict]:
        """Получить письма за последние N часов"""
        try:
            query = f'newer_than:{hours}h'
            results = self.service.users().messages().list(userId='me', q=query).execute()
            messages = results.get('messages', [])
            
            emails = []
            for message in messages:
                msg = self.service.users().messages().get(userId='me', id=message['id']).execute()
                emails.append(msg)
            
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
