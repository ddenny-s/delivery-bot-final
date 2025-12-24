"""
Gmail API клиент
"""
import base64
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials as UserCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.exceptions import RefreshError
from google.api_python_client import discovery
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


class GmailClient:
    """Клиент для работы с Gmail API"""
    
    def __init__(self, credentials_file: str = 'credentials.json', token_file: str = 'token.json'):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self.authenticate()
    
    def authenticate(self):
        """Авторизация с Gmail API"""
        creds = None
        
        if os.path.exists(self.token_file):
            creds = UserCredentials.from_authorized_user_file(self.token_file, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except RefreshError:
                    creds = None
            
            if not creds:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
        
        self.service = discovery.build('gmail', 'v1', credentials=creds)
        logger.info("✅ Gmail клиент инициализирован")
    
    def get_emails_since(self, hours: int = 24) -> List[Dict]:
        """Получить письма за последние N часов"""
        try:
            query = f'newer_than:{hours}h'
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=50
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for message in messages:
                email_data = self.parse_message(message['id'])
                if email_data:
                    emails.append(email_data)
            
            logger.info(f"✅ Получено {len(emails)} писем")
            return emails
        except Exception as e:
            logger.error(f"❌ Ошибка при получении писем: {e}")
            return []
    
    def parse_message(self, message_id: str) -> Optional[Dict]:
        """Парсить одно письмо"""
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            headers = message['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'Без темы')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Неизвестно')
            
            body = self.get_message_body(message)
            
            return {
                'id': message_id,
                'subject': subject,
                'sender': sender,
                'body': body
            }
        except Exception as e:
            logger.error(f"❌ Ошибка при парсинге письма: {e}")
            return None
    
    def get_message_body(self, message: Dict) -> str:
        """Извлечь текст письма"""
        try:
            if 'parts' in message['payload']:
                parts = message['payload']['parts']
                data = ''
                for part in parts:
                    if part['mimeType'] == 'text/plain':
                        if 'data' in part['body']:
                            data = part['body']['data']
                            break
                    elif part['mimeType'] == 'text/html':
                        if 'data' in part['body']:
                            data = part['body']['data']
            else:
                data = message['payload']['body'].get('data', '')
            
            if data:
                text = base64.urlsafe_b64decode(data).decode('utf-8')
                soup = BeautifulSoup(text, 'html.parser')
                return soup.get_text()
            return ''
        except Exception as e:
            logger.error(f"❌ Ошибка при извлечении текста: {e}")
            return ''
