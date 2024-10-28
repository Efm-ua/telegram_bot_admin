from django.core.management.base import BaseCommand
from django.conf import settings
import asyncio
import logging
import sys
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Глобальна змінна для зберігання додатку
application = None

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник команди /start"""
    user = update.effective_user
    await update.message.reply_text(
        f'Привіт, {user.first_name}! 👋\n'
        f'Це тестовий бот для адмін-панелі.'
    )

async def stop_bot():
    """Зупинка бота"""
    global application
    if application:
        await application.stop()
        await application.shutdown()

async def run_bot(token: str):
    """Запуск бота"""
    global application
    
    # Створюємо додаток
    application = (
        Application.builder()
        .token(token)
        .build()
    )

    # Додаємо обробники
    application.add_handler(CommandHandler("start", start_command))

    # Запускаємо бота
    await application.initialize()
    await application.start()
    await application.run_polling(drop_pending_updates=True)

class Command(BaseCommand):
    help = 'Запускає Telegram бота'

    def handle(self, *args, **options):
        """Запуск команди"""
        # Налаштування для Windows
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        self.stdout.write(self.style.SUCCESS('Запуск бота...'))

        # Отримуємо токен з налаштувань
        token = settings.TELEGRAM_BOT_TOKEN

        # Створюємо новий event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Запускаємо бота
            loop.run_until_complete(run_bot(token))
        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS('\nОтримано сигнал завершення...'))
            # Зупиняємо бота
            loop.run_until_complete(stop_bot())
        finally:
            # Закриваємо event loop
            loop.close()
            self.stdout.write(self.style.SUCCESS('Бот зупинений'))