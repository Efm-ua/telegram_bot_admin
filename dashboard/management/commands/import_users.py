from django.core.management.base import BaseCommand
import json
from dashboard.models import TelegramUser, Statistics
from django.utils import timezone
from django.db import transaction
from datetime import datetime
import os

class Command(BaseCommand):
    help = 'Import users from JSON file'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Path to the JSON file')

    def handle(self, *args, **options):
        file_path = options['json_file']
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                
            users_data = data.get('users', {})
            statistics_data = data.get('statistics', {})

            with transaction.atomic():
                # Імпорт користувачів
                imported_count = 0
                updated_count = 0
                
                for user_id, user_data in users_data.items():
                    try:
                        # Конвертуємо дату
                        join_date = datetime.fromisoformat(user_data.get('join_date')) if user_data.get('join_date') else timezone.now()
                        
                        # Створюємо або оновлюємо користувача
                        user, created = TelegramUser.objects.update_or_create(
                            user_id=int(user_id),
                            defaults={
                                'username': user_data.get('username'),
                                'language': user_data.get('language', 'en'),
                                'tokens': user_data.get('tokens', 5000),
                                'referral_code': user_data.get('referral_code'),
                                'join_date': join_date,
                                'is_active': True,
                            }
                        )
                        
                        if created:
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'Created new user: {user_id}'
                                )
                            )
                            imported_count += 1
                        else:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'Updated existing user: {user_id}'
                                )
                            )
                            updated_count += 1
                            
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f'Error processing user {user_id}: {str(e)}'
                            )
                        )

                # Оновлюємо зв'язки рефералів
                for user_id, user_data in users_data.items():
                    if user_data.get('referred_by'):
                        try:
                            user = TelegramUser.objects.get(user_id=int(user_id))
                            referrer = TelegramUser.objects.get(
                                user_id=int(user_data['referred_by'])
                            )
                            user.referred_by = referrer
                            user.save()
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'Updated referral for user: {user_id}'
                                )
                            )
                        except TelegramUser.DoesNotExist:
                            self.stdout.write(
                                self.style.ERROR(
                                    f'Could not find user or referrer for {user_id}'
                                )
                            )
                            continue

                # Оновлюємо статистику
                if statistics_data:
                    try:
                        stats, created = Statistics.objects.get_or_create(
                            date=timezone.now().date(),
                            defaults={
                                'total_bot_users': statistics_data.get('total_bot_users', 0),
                                'webapp_opens': statistics_data.get('webapp_opens', 0),
                                'ru_users': statistics_data.get('languages', {}).get('ru', 0),
                                'ua_users': statistics_data.get('languages', {}).get('ua', 0),
                                'en_users': statistics_data.get('languages', {}).get('en', 0),
                                'total_spots': data.get('total_spots', 10000),
                                'used_spots': data.get('used_spots', 0),
                            }
                        )
                        if created:
                            self.stdout.write(
                                self.style.SUCCESS('Created new statistics entry')
                            )
                        else:
                            self.stdout.write(
                                self.style.SUCCESS('Updated statistics entry')
                            )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'Error updating statistics: {str(e)}')
                        )

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Import completed!\n'
                        f'Successfully imported {imported_count} new users\n'
                        f'Updated {updated_count} existing users\n'
                        f'Total users in database: {TelegramUser.objects.count()}'
                    )
                )

        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(f'File not found: {file_path}')
            )
        except json.JSONDecodeError:
            self.stdout.write(
                self.style.ERROR(f'Invalid JSON format in file: {file_path}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {str(e)}')
            )