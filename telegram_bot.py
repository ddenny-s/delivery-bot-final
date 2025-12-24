"""
Telegram бот с командами
"""
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import TelegramError
import logging
from database import DatabaseManager

logger = logging.getLogger(__name__)


class DeliveryTelegramBot:
    """Telegram бот"""
    
    def __init__(self, bot_token: str, db_manager: DatabaseManager):
        self.bot_token = bot_token
        self.db = db_manager
        self.application = None
    
    async def setup_commands(self):
        """Установить команды"""
        commands = [
            BotCommand("start", "🚀 Начать"),
            BotCommand("check", "🔍 Проверить доставки"),
            BotCommand("status", "📦 Активные доставки"),
            BotCommand("stats", "📊 Статистика"),
            BotCommand("mark_done", "✅ Отметить как забранную"),
            BotCommand("delete", "🗑️ Удалить доставку"),
            BotCommand("help", "❓ Справка"),
        ]
        await self.application.bot.set_my_commands(commands)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start"""
        message = """🚀 <b>Delivery Bot</b>

Я помогу тебе отслеживать доставки!

<b>Команды:</b>
/check - Проверить доставки
/status - Активные доставки
/stats - Статистика
/mark_done - Отметить как забранную
/delete - Удалить доставку
/help - Справка"""
        await update.message.reply_text(message, parse_mode='HTML')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /help"""
        message = """<b>📖 Справка</b>

/check - Проверить доставки прямо сейчас
/status - Показать активные доставки
/stats - Статистика по доставкам
/mark_done &lt;номер&gt; - Отметить как забранную
/delete &lt;номер&gt; - Удалить доставку"""
        await update.message.reply_text(message, parse_mode='HTML')
    
    async def check_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /check"""
        await update.message.reply_text("🔄 Проверяю доставки...")
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /status"""
        deliveries = self.db.get_active_deliveries()
        
        if not deliveries:
            await update.message.reply_text("📭 Нет активных доставок", parse_mode='HTML')
            return
        
        message = "<b>📦 Активные доставки:</b>\n\n"
        for i, delivery in enumerate(deliveries, 1):
            message += f"<b>{i}. {delivery.service}</b>\n"
            message += f"   Номер: <code>{delivery.order_number}</code>\n"
            message += f"   Статус: {delivery.status}\n"
            if delivery.address:
                message += f"   Адрес: {delivery.address}\n"
            if delivery.pickup_code:
                message += f"   Код: <code>{delivery.pickup_code}</code>\n"
            message += "\n"
        
        await update.message.reply_text(message, parse_mode='HTML')
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /stats"""
        stats = self.db.get_statistics()
        
        message = "<b>📊 Статистика:</b>\n\n"
        message += f"📦 Всего: <b>{stats['всего']}</b>\n"
        message += f"✅ Активных: <b>{stats['активных']}</b>\n"
        message += f"🎉 Завершенных: <b>{stats['завершенных']}</b>\n"
        
        if stats['по_сервисам']:
            message += "\n<b>По сервисам:</b>\n"
            for service, count in stats['по_сервисам'].items():
                message += f"  • {service}: {count}\n"
        
        await update.message.reply_text(message, parse_mode='HTML')
    
    async def mark_done_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /mark_done"""
        if not context.args:
            await update.message.reply_text("❌ Укажи номер заказа\nПример: /mark_done 123456789", parse_mode='HTML')
            return
        
        order_number = context.args[0]
        if self.db.mark_as_inactive(order_number):
            await update.message.reply_text(f"✅ Доставка <code>{order_number}</code> отмечена!", parse_mode='HTML')
        else:
            await update.message.reply_text(f"❌ Доставка <code>{order_number}</code> не найдена", parse_mode='HTML')
    
    async def delete_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /delete"""
        if not context.args:
            await update.message.reply_text("❌ Укажи номер заказа\nПример: /delete 123456789", parse_mode='HTML')
            return
        
        order_number = context.args[0]
        if self.db.delete_delivery(order_number):
            await update.message.reply_text(f"🗑️ Доставка <code>{order_number}</code> удалена!", parse_mode='HTML')
        else:
            await update.message.reply_text(f"❌ Доставка <code>{order_number}</code> не найдена", parse_mode='HTML')
    
    async def initialize(self):
        """Инициализировать"""
        self.application = Application.builder().token(self.bot_token).build()
        
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("check", self.check_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("mark_done", self.mark_done_command))
        self.application.add_handler(CommandHandler("delete", self.delete_command))
        
        await self.setup_commands()
        logger.info("✅ Telegram бот инициализирован")
    
    async def start(self):
        """Запустить"""
        await self.initialize()
        await self.application.run_polling()
    
    async def send_message(self, chat_id: int, message: str) -> bool:
        """Отправить сообщение"""
        try:
            await self.application.bot.send_message(chat_id=chat_id, text=message, parse_mode='HTML')
            return True
        except TelegramError as e:
            logger.error(f"❌ Ошибка Telegram: {e}")
            return False
