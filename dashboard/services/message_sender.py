import asyncio
from typing import List, Dict, Optional
from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import TelegramError, RetryAfter
from django.conf import settings
from django.utils import timezone
from ..models import TelegramUser, UserActivity

class MessageSender:
    def __init__(self, bot_token: str = None):
        self.bot_token = bot_token or settings.TELEGRAM_BOT_TOKEN
        self.bot = None
        self.DELAY_BETWEEN_MESSAGES = 0.05  # 50ms між повідомленнями
        self.MESSAGES_PER_SECOND = 30  # максимум повідомлень в секунду

    async def initialize(self):
        """Ініціалізація бота"""
        self.bot = Bot(token=self.bot_token)

    async def send_message(self, user_id: int, text: str, photo_url: Optional[str] = None, 
                         buttons: Optional[dict] = None) -> bool:
        """Відправка повідомлення користувачу"""
        try:
            if buttons:
                # Створюємо розмітку клавіатури
                keyboard = []
                for row in buttons.get('inline_keyboard', []):
                    keyboard_row = []
                    for button in row:
                        keyboard_row.append(
                            InlineKeyboardButton(
                                text=button['text'],
                                url=button.get('url'),
                                callback_data=button.get('callback_data')
                            )
                        )
                    keyboard.append(keyboard_row)
                reply_markup = InlineKeyboardMarkup(keyboard)
            else:
                reply_markup = None

            if photo_url:
                await self.bot.send_photo(
                    chat_id=user_id,
                    photo=photo_url,
                    caption=text,
                    reply_markup=reply_markup
                )
            else:
                await self.bot.send_message(
                    chat_id=user_id,
                    text=text,
                    reply_markup=reply_markup
                )
            return True
            
        except RetryAfter as e:
            # Якщо досягнуто ліміт, чекаємо вказаний час
            await asyncio.sleep(e.retry_after)
            return await self.send_message(user_id, text, photo_url, buttons)
            
        except TelegramError as e:
            print(f"Error sending message to {user_id}: {e}")
            return False

    async def send_bulk_message(self, users: List[TelegramUser], text: str, 
                              photo_url: Optional[str] = None, 
                              buttons: Optional[dict] = None) -> Dict:
        """Масова розсилка повідомлень"""
        results = {
            'total': len(users),
            'sent': 0,
            'failed': 0,
            'inactive': 0
        }

        await self.initialize()

        # Розбиваємо користувачів на групи
        batch_size = self.MESSAGES_PER_SECOND
        for i in range(0, len(users), batch_size):
            batch = users[i:i + batch_size]
            
            for user in batch:
                if not user.is_active:
                    results['inactive'] += 1
                    continue

                success = await self.send_message(user.user_id, text, photo_url, buttons)
                
                if success:
                    results['sent'] += 1
                    # Записуємо активність
                    await asyncio.to_thread(
                        UserActivity.objects.create,
                        user=user,
                        action_type='message_received'
                    )
                else:
                    results['failed'] += 1

                # Пауза між повідомленнями
                await asyncio.sleep(self.DELAY_BETWEEN_MESSAGES)

            # Пауза між групами
            if i + batch_size < len(users):
                await asyncio.sleep(1)  # 1 секунда між групами

        return results