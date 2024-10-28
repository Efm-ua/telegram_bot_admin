import json
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from dashboard.models import TelegramUser, Statistics
from datetime import date

class Command(BaseCommand):
    help = 'Імпортує дані з JSON файлу'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Шлях до JSON файлу')

    def handle(self, *args, **options):
        self.stdout.write('Читаємо JSON файл...')
        try:
            with open(options['json_file'], 'r', encoding='utf-8') as file:
                data = json.load(file)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Помилка читання файлу: {e}'))
            return

        # Імпорт користувачів
        self.stdout.write('Імпортуємо користувачів...')
        users_created = 0
        users_updated = 0

        for user_id, user_data in data['users'].items():
            try:
                # Спочатку створюємо користувача без referrals
                defaults = {
                    'username': user_data.get('username'),
                    'language': user_data.get('language', 'en'),
                    'tokens': user_data.get('tokens', 5000),
                    'referral_code': f"REF{user_id}",
                    'join_date': parse_datetime(user_data.get('join_date')),
                    'is_active': True
                }

                user, created = TelegramUser.objects.update_or_create(
                    user_id=int(user_id),
                    defaults=defaults
                )

                if created:
                    users_created += 1
                else:
                    users_updated += 1

            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Помилка при імпорті користувача {user_id}: {e}')
                )

        # Встановлюємо зв'язки referrals
        self.stdout.write("Встановлюємо реферальні зв'язки...")
        for user_id, user_data in data['users'].items():
            if user_data.get('referred_by'):
                try:
                    user = TelegramUser.objects.get(user_id=int(user_id))
                    referrer = TelegramUser.objects.get(
                        user_id=int(user_data['referred_by'])
                    )
                    user.referred_by = referrer
                    user.save()
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Помилка при встановленні реферала для {user_id}: {e}'
                        )
                    )

        # Імпорт статистики
        self.stdout.write('Імпортуємо статистику...')
        try:
            stats = data['statistics']
            Statistics.objects.update_or_create(
                date=date.today(),
                defaults={
                    'total_bot_users': stats.get('total_bot_users', 0),
                    'webapp_opens': stats.get('webapp_opens', 0),
                    'ru_users': stats.get('languages', {}).get('ru', 0),
                    'ua_users': stats.get('languages', {}).get('ua', 0),
                    'en_users': stats.get('languages', {}).get('en', 0),
                    'total_spots': data.get('total_spots', 10000),
                    'used_spots': data.get('used_spots', 0)
                }
            )
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Помилка при імпорті статистики: {e}')
            )

        # Підсумок
        self.stdout.write(
            self.style.SUCCESS(
                f'Імпорт завершено:\n'
                f'- Створено нових користувачів: {users_created}\n'
                f'- Оновлено існуючих користувачів: {users_updated}\n'
                f'- Імпортовано статистику'
            )
        )