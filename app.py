"""
Flask приложение для Cloud Run
"""
from flask import Flask, jsonify
import asyncio
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Глобальные переменные
db = None
gmail_client = None
parser = None
telegram_bot = None


def init_components():
    """Инициализировать компоненты"""
    global db, gmail_client, parser, telegram_bot
    
    try:
        from config import Config
        from gmail_client import GmailClient
        from delivery_parser import DeliveryParser
        from telegram_bot import DeliveryTelegramBot
        from database import DatabaseManager
        
        logger.info("🔧 Инициализирую компоненты...")
        
        # Проверяем конфиг
        config_valid = Config.validate()
        
        if not config_valid:
            logger.warning("⚠️ Не все переменные установлены, но приложение запустится в режиме health check")
            return True  # Возвращаем True, чтобы приложение запустилось
        
        try:
            db = DatabaseManager(Config.DATABASE_URL)
            logger.info("✅ БД инициализирована")
        except Exception as e:
            logger.warning(f"⚠️ Ошибка инициализации БД: {e}")
        
        try:
            gmail_client = GmailClient(Config.GMAIL_CREDENTIALS, Config.GMAIL_TOKEN)
            logger.info("✅ Gmail клиент инициализирован")
        except Exception as e:
            logger.warning(f"⚠️ Ошибка инициализации Gmail: {e}")
        
        try:
            if Config.OPENAI_API_KEY:
                parser = DeliveryParser(Config.OPENAI_API_KEY)
                logger.info("✅ Парсер инициализирован")
        except Exception as e:
            logger.warning(f"⚠️ Ошибка инициализации парсера: {e}")
        
        try:
            if Config.TELEGRAM_BOT_TOKEN:
                telegram_bot = DeliveryTelegramBot(Config.TELEGRAM_BOT_TOKEN, db)
                logger.info("✅ Telegram бот инициализирован")
        except Exception as e:
            logger.warning(f"⚠️ Ошибка инициализации Telegram: {e}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации: {e}")
        return True  # Все равно возвращаем True, чтобы приложение запустилось


# Инициализируем при старте
init_components()


@app.route('/', methods=['GET'])
def health_check():
    """Проверка здоровья"""
    return jsonify({'status': 'ok', 'message': 'Delivery Bot is running'}), 200


@app.route('/check', methods=['POST'])
def check_deliveries():
    """Ручная проверка доставок"""
    try:
        if not all([db, gmail_client, parser, telegram_bot]):
            return jsonify({'status': 'error', 'message': 'Components not initialized'}), 500
        
        logger.info("🔍 Проверяю доставки...")
        
        # Получаем письма
        emails = gmail_client.get_emails_since(hours=24)
        if not emails:
            logger.info("📭 Писем не найдено")
            return jsonify({'status': 'ok', 'message': 'No emails found', 'count': 0}), 200
        
        # Парсим письма
        deliveries = parser.batch_parse_emails(emails)
        logger.info(f"✅ Найдено {len(deliveries)} доставок")
        
        # Сохраняем и отправляем
        count = 0
        for delivery in deliveries:
            db.add_delivery(delivery)
            message = parser.format_for_telegram(delivery)
            # Отправляем асинхронно
            asyncio.run(telegram_bot.send_message(Config.TELEGRAM_CHAT_ID, message))
            count += 1
        
        return jsonify({'status': 'ok', 'message': f'Processed {count} deliveries', 'count': count}), 200
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/status', methods=['GET'])
def get_status():
    """Получить статус доставок"""
    try:
        if not db:
            return jsonify({'status': 'error'}), 500
        
        stats = db.get_statistics()
        return jsonify({'status': 'ok', 'data': stats}), 200
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/mark_done/<order_number>', methods=['POST'])
def mark_done(order_number):
    """Отметить доставку как забранную"""
    try:
        if not db:
            return jsonify({'status': 'error'}), 500
        
        if db.mark_as_inactive(order_number):
            return jsonify({'status': 'ok', 'message': f'Delivery {order_number} marked as done'}), 200
        else:
            return jsonify({'status': 'error', 'message': 'Delivery not found'}), 404
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/delete/<order_number>', methods=['DELETE'])
def delete_delivery(order_number):
    """Удалить доставку"""
    try:
        if not db:
            return jsonify({'status': 'error'}), 500
        
        if db.delete_delivery(order_number):
            return jsonify({'status': 'ok', 'message': f'Delivery {order_number} deleted'}), 200
        else:
            return jsonify({'status': 'error', 'message': 'Delivery not found'}), 404
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    """404 ошибка"""
    return jsonify({'status': 'error', 'message': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """500 ошибка"""
    return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"🚀 Запускаю Flask на порту {port}")
    app.run(host='0.0.0.0', port=port, debug=False)