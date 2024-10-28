from telegram.ext import Application, CommandHandler, ContextTypes
from telegram import Update
import logging
import asyncio

logger = logging.getLogger(__name__)

class TelegramBotHandler:
    def __init__(self, token):
        self.token = token
        self._running = True
        self._application = None
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обробка команди /start"""
        user = update.effective_user
        await update.message.reply_text(
            f'Привіт, {user.first_name}! 👋\n'
            f'Це тестовий бот для адмін-панелі.'
        )

    async def _run_polling(self):
        """Внутрішній метод для запуску polling"""
        while self._running:
            try:
                await self._application.run_polling(allowed_updates=Update.ALL_TYPES)
            except Exception as e:
                logger.error(f"Polling error: {e}")
                if self._running:
                    await asyncio.sleep(5)  # Пауза перед повторною спробою

    async def start(self):
        """Запуск бота"""
        logger.info("Бот запускається...")
        
        self._application = (
            Application.builder()
            .token(self.token)
            .build()
        )
        
        self._application.add_handler(CommandHandler('start', self.start_command))
        
        async with self._application:
            await self._application.start()
            logger.info("Бот успішно запущений")
            await self._run_polling()

    async def stop(self):
        """Зупинка бота"""
        self._running = False
        if self._application:
            await self._application.stop()
            logger.info("Бот зупинений")