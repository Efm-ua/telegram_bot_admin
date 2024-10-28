import asyncio
from typing import List, Dict
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError
from django.conf import settings
from django.utils import timezone
from ..models import TelegramUser

class StatusChecker:
    def __init__(self, bot_token: str = None):
        self.bot_token = bot_token or settings.TELEGRAM_BOT_TOKEN
        self.bot = None
        self.chat_id = "@daodrophelper"  # ID вашого чату

    async def initialize(self):
        """Ініціалізація бота"""
        self.bot = Bot(token=self.bot_token)

    async def check_user_bot_status(self, user: TelegramUser) -> bool:
        """Перевірка чи користувач не видалив бота"""
        try:
            await self.bot.send_chat_action(chat_id=user.user_id, action="typing")
            return True
        except TelegramError:
            return False

    async def check_user_chat_membership(self, user: TelegramUser) -> bool:
        """Перевірка чи користувач в чаті"""
        try:
            member = await self.bot.get_chat_member(chat_id=self.chat_id, user_id=user.user_id)
            return member.status in ['member', 'administrator', 'creator']
        except TelegramError:
            return False

    async def check_users_status(self, users: List[TelegramUser]) -> Dict:
        """Перевірка статусу групи користувачів"""
        results = {
            'total': len(users),
            'checked': 0,
            'active_bot': 0,
            'inactive_bot': 0,
            'in_chat': 0,
            'not_in_chat': 0
        }

        await self.initialize()
        
        for user in users:
            # Перевірка статусу бота
            is_bot_active = await self.check_user_bot_status(user)
            is_in_chat = await self.check_user_chat_membership(user)
            
            # Оновлення статусів
            was_active = user.is_active
            was_in_chat = user.in_chat
            
            user.is_active = is_bot_active
            user.in_chat = is_in_chat
            user.last_status_check = timezone.now()
            
            # Оновлення дат зміни статусу
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
            
            # Оновлення статистики
            results['checked'] += 1
            if is_bot_active:
                results['active_bot'] += 1
            else:
                results['inactive_bot'] += 1
            if is_in_chat:
                results['in_chat'] += 1
            else:
                results['not_in_chat'] += 1

        return results