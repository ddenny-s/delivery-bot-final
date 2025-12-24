"""
Парсер доставок с GPT
"""
import json
import re
from typing import Dict, Optional, List
from openai import OpenAI
import logging

logger = logging.getLogger(__name__)


class DeliveryParser:
    """Парсер для извлечения информации о доставках"""
    
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"
    
    def parse_delivery_email(self, email_data: Dict) -> Optional[Dict]:
        """Парсить письмо о доставке с помощью GPT"""
        subject = email_data.get('subject', '')
        body = email_data.get('body', '')
        sender = email_data.get('sender', '')
        
        full_text = f"Тема: {subject}\n\nОт: {sender}\n\nТекст:\n{body}"
        
        prompt = f"""Проанализируй это письмо и извлеки информацию о доставке.

Письмо:
{full_text}

Извлеки следующую информацию если она есть:
1. delivery_service: Название сервиса доставки
2. order_number: Номер заказа/трекинга
3. delivery_address: Адрес доставки
4. delivery_status: Текущий статус
5. pickup_code: Код для забора если есть
6. estimated_delivery: Ожидаемая дата/время доставки
7. recipient_name: Имя получателя
8. is_delivery_email: true/false - это письмо о доставке?

Верни ТОЛЬКО валидный JSON, ничего больше. Если поле не найдено, используй null.

Пример:
{{
    "is_delivery_email": true,
    "delivery_service": "DPD",
    "order_number": "123456789",
    "delivery_address": "ул. Главная, 123",
    "delivery_status": "В пути",
    "pickup_code": "1234",
    "estimated_delivery": "2025-12-25",
    "recipient_name": "Иван Петров"
}}"""
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = response.content[0].text.strip()
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            
            if json_match:
                parsed_data = json.loads(json_match.group())
                if parsed_data.get('is_delivery_email'):
                    return parsed_data
            
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка парсинга: {e}")
            return None
    
    def format_for_telegram(self, delivery_info: Dict) -> str:
        """Форматировать для Telegram"""
        service = delivery_info.get('delivery_service', 'Неизвестно')
        order_num = delivery_info.get('order_number', 'N/A')
        address = delivery_info.get('delivery_address', 'N/A')
        status = delivery_info.get('delivery_status', 'N/A')
        pickup_code = delivery_info.get('pickup_code')
        estimated = delivery_info.get('estimated_delivery', 'N/A')
        recipient = delivery_info.get('recipient_name', 'N/A')
        
        message = f"""📦 <b>Обновление доставки</b>

<b>Сервис:</b> {service}
<b>Номер заказа:</b> <code>{order_num}</code>
<b>Статус:</b> {status}
<b>Получатель:</b> {recipient}
<b>Адрес:</b> {address}
<b>Ожидаемо:</b> {estimated}"""
        
        if pickup_code:
            message += f"\n<b>Код забора:</b> <code>{pickup_code}</code>"
        
        return message
    
    def batch_parse_emails(self, emails: List[Dict]) -> List[Dict]:
        """Парсить несколько писем"""
        delivery_emails = []
        for email in emails:
            parsed = self.parse_delivery_email(email)
            if parsed:
                delivery_emails.append(parsed)
        return delivery_emails
