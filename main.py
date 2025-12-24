"""
Главный файл бота
"""
import asyncio
import logging
from config import Config
from gmail_client import GmailClient
from delivery_parser import DeliveryParser
from telegram_bot import DeliveryTelegramBot
from database import DatabaseManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('delivery_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DeliveryBot:
    """Главный класс бота"""
    
    def __init__(self):
        """Инициализация"""
        Config.validate()
        
        self.db = DatabaseManager(Config.DATABASE_URL)
        self.gmail_client = GmailClient(Config.GMAIL_CREDENTIALS, Config.GMAIL_TOKEN)
        self.parser = DeliveryParser(Config.OPENAI_API_KEY)
        self.telegram_bot = DeliveryTelegramBot(Config.TELEGRAM_BOT_TOKEN, self.db)
        
        logger.info("✅ Бот инициализирован")
    
    async def check_deliveries(self, hours: int = 24) -> int:
        """Проверить доставки"""
        logger.info(f"🔍 Проверяю доставки за {hours} часов...")
        
        try:
            emails = self.gmail_client.get_emails_since(hours=hours)
            if not emails:
                logger.info("📭 Писем не найдено")
                return 0
            
            deliveries = self.parser.batch_parse_emails(emails)
            logger.info(f"✅ Найдено {len(deliveries)} доставок")
            
            count = 0
            for delivery in deliveries:
                self.db.add_delivery(delivery)
                message = self.parser.format_for_telegram(delivery)
                await self.telegram_bot.send_message(Config.TELEGRAM_CHAT_ID, message)
                count += 1
            
            return count
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")
            return 0
    
    async def run(self):
        """Запустить"""
        logger.info("🚀 Запускаю бота...")
        await self.telegram_bot.start()


async def main():
    """Главная функция"""
    try:
        bot = DeliveryBot()
        await bot.run()
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
