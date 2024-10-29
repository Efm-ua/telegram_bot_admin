import asyncio
from typing import List, Dict, Set
from datetime import datetime
import math
from telegram import Bot
from telegram.error import TelegramError, RetryAfter
from django.conf import settings
from django.utils import timezone
from ..models import TelegramUser

class StatusChecker:
    def __init__(self, bot_token: str = None):
        self.bot_token = bot_token or settings.TELEGRAM_BOT_TOKEN
        self.bot = Bot(token=self.bot_token)  # Ініціалізуємо бота відразу
        self.chat_id = "@daodrophelper"
        self.BATCH_SIZE = 30
        self.DELAY_BETWEEN_REQUESTS = 0.034
        self.DELAY_BETWEEN_BATCHES = 0.1

    async def process_batch(self, users_batch: List[TelegramUser], progress_callback=None) -> Dict:
        """Обробка однієї пачки користувачів"""
        results = {
            'checked': 0,
            'active_bot': 0,
            'inactive_bot': 0,
            'in_chat': 0,
            'not_in_chat': 0
        }

        # Створюємо таски для всіх користувачів в пачці
        tasks = []
        for user in users_batch:
            tasks.append(self.check_single_user(user))
        
        # Виконуємо всі таски паралельно
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Обробляємо результати
        for result in batch_results:
            if isinstance(result, dict):  # якщо немає помилки
                for key in results:
                    results[key] += result[key]
            
        return results

    async def check_single_user(self, user: TelegramUser) -> Dict:
        """Перевірка одного користувача"""
        result = {
            'checked': 0,
            'active_bot': 0,
            'inactive_bot': 0,
            'in_chat': 0,
            'not_in_chat': 0
        }

        try:
            # Перевірка статусу бота
            is_bot_active = False
            try:
                await self.bot.send_chat_action(chat_id=user.user_id, action="typing")
                is_bot_active = True
            except RetryAfter as e:
                await asyncio.sleep(e.retry_after)
                return result
            except TelegramError:
                pass

            await asyncio.sleep(self.DELAY_BETWEEN_REQUESTS)

            # Перевірка участі в чаті
            is_in_chat = False
            try:
                member = await self.bot.get_chat_member(chat_id=self.chat_id, user_id=user.user_id)
                is_in_chat = member.status in ['member', 'administrator', 'creator']
            except RetryAfter as e:
                await asyncio.sleep(e.retry_after)
                return result
            except TelegramError:
                pass

            # Оновлення статусів
            was_active = user.is_active
            was_in_chat = user.in_chat
            
            user.is_active = is_bot_active
            user.in_chat = is_in_chat
            user.last_status_check = timezone.now()
            
            if was_active and not is_bot_active:
                user.deleted_bot_at = timezone.now()
            elif not was_active and is_bot_active:
                user.deleted_bot_at = None
                
            if was_in_chat and not is_in_chat:
                user.left_chat_at = timezone.now()
            elif not was_in_chat and is_in_chat:
                user.left_chat_at = None
                user.chat_join_date = timezone.now()
            
            await asyncio.to_thread(user.save)
            
            # Оновлення результатів
            result['checked'] = 1
            if is_bot_active:
                result['active_bot'] = 1
            else:
                result['inactive_bot'] = 1
            if is_in_chat:
                result['in_chat'] = 1
            else:
                result['not_in_chat'] = 1

        except Exception as e:
            print(f"Error processing user {user.user_id}: {str(e)}")

        return result

    async def check_users_status(self, users: List[TelegramUser], progress_callback=None) -> Dict:
        """Перевірка статусу всіх користувачів з урахуванням лімітів"""
        total_results = {
            'total': len(users),
            'checked': 0,
            'active_bot': 0,
            'inactive_bot': 0,
            'in_chat': 0,
            'not_in_chat': 0
        }

        # Розбиваємо користувачів на пачки
        batches = [users[i:i + self.BATCH_SIZE] for i in range(0, len(users), self.BATCH_SIZE)]
        total_batches = len(batches)

        for i, batch in enumerate(batches, 1):
            # Обробка пачки
            batch_results = await self.process_batch(batch, progress_callback)
            
            # Оновлення загальної статистики
            for key in ['checked', 'active_bot', 'inactive_bot', 'in_chat', 'not_in_chat']:
                total_results[key] += batch_results[key]

            # Пауза між пачками
            if i < total_batches:  # Не чекаємо після останньої пачки
                await asyncio.sleep(self.DELAY_BETWEEN_BATCHES)

        return total_results