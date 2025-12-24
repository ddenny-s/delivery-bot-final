"""
Конфигурация - получает ВСЁ из Google Cloud Secret Manager
"""
import os
from google.cloud import secretmanager
import logging

logger = logging.getLogger(__name__)


class Config:
    """Конфигурация приложения"""
    
    @staticmethod
    def get_secret(secret_id: str, version_id: str = "latest") -> str:
        """
        Получить секрет из Google Cloud Secret Manager
        
        Args:
            secret_id: ID секрета
            version_id: Версия секрета
        
        Returns:
            Значение секрета
        """
        try:
            project_id = os.environ.get("GCP_PROJECT_ID")
            
            if not project_id:
                logger.warning("GCP_PROJECT_ID не установлен, используем локальные переменные")
                return os.environ.get(secret_id, "")
            
            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
            response = client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            logger.warning(f"Не удалось получить секрет {secret_id} из Google Cloud: {e}")
            logger.warning(f"Используем переменную окружения {secret_id}")
            return os.environ.get(secret_id, "")
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
    
    # Telegram Configuration
    TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "0")
    
    # Gmail Configuration
    GMAIL_CREDENTIALS = os.environ.get("GMAIL_CREDENTIALS", "credentials.json")
    GMAIL_TOKEN = os.environ.get("GMAIL_TOKEN", "token.json")
    
    # Database Configuration
    DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///deliveries.db")
    
    # Bot Configuration
    CHECK_INTERVAL_HOURS = int(os.environ.get("CHECK_INTERVAL_HOURS", "24"))
    DAILY_CHECK_TIME = os.environ.get("DAILY_CHECK_TIME", "09:00")
    
    # Google Cloud Configuration
    GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "")
    
    @classmethod
    def validate(cls):
        """Проверить что все необходимые конфиги установлены"""
        required = [
            ("OPENAI_API_KEY", cls.OPENAI_API_KEY),
            ("TELEGRAM_BOT_TOKEN", cls.TELEGRAM_BOT_TOKEN),
            ("TELEGRAM_CHAT_ID", cls.TELEGRAM_CHAT_ID),
        ]
        
        missing = [name for name, value in required if not value]
        
        if missing:
            logger.warning(f"⚠️ Отсутствуют переменные: {', '.join(missing)}")
            return False
        
        logger.info("✅ Все конфиги установлены")
        return True