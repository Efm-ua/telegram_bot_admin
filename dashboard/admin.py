from asgiref.sync import sync_to_async
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Q
from django.urls import reverse, path
from django.template.response import TemplateResponse
from django.contrib import messages
from django.shortcuts import redirect
import asyncio
from .models import TelegramUser, Statistics, UserActivity
from .services.status_checker import StatusChecker
from .services.message_sender import MessageSender
from .forms import MessageForm
import os

@admin.action(description="Перевірити статус вибраних користувачів")
def check_users_status(modeladmin, request, queryset):
    """Масова перевірка статусу користувачів"""
    async def async_check():
        try:
            checker = StatusChecker()
            users_count = await sync_to_async(queryset.count)()
            
            await sync_to_async(messages.info)(
                request, 
                f'Починаємо перевірку {users_count} користувачів. '
                f'Це займе приблизно {(users_count / 30):.1f} секунд'
            )

            # Конвертуємо queryset в список
            users_list = await sync_to_async(list)(queryset)

            # Запускаємо перевірку
            results = await checker.check_users_status(users_list)

            message = (
                f"Перевірено {results['checked']} користувачів:\n"
                f"Активні боти: {results['active_bot']}\n"
                f"Неактивні боти: {results['inactive_bot']}\n"
                f"У чаті: {results['in_chat']}\n"
                f"Не в чаті: {results['not_in_chat']}"
            )
            await sync_to_async(messages.success)(request, message)
            
        except Exception as e:
            await sync_to_async(messages.error)(
                request, 
                f"Помилка при перевірці: {str(e)}"
            )

    # Запускаємо асинхронну функцію
    asyncio.run(async_check())

@admin.action(description="Відправити повідомлення вибраним користувачам")
def send_message_to_users(modeladmin, request, queryset):
    """Відправка повідомлення вибраним користувачам"""
    selected = queryset.values_list('pk', flat=True)
    return redirect(
        f'send-message/?ids={",".join(str(pk) for pk in selected)}'
    )

class HasReferralsFilter(admin.SimpleListFilter):
    title = 'Наявність рефералів'
    parameter_name = 'has_referrals'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Є реферали'),
            ('no', 'Немає рефералів'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.annotate(refs_count=Count('referrals')).filter(refs_count__gt=0)
        if self.value() == 'no':
            return queryset.annotate(refs_count=Count('referrals')).filter(refs_count=0)

class UserStatusFilter(admin.SimpleListFilter):
    title = 'Статус користувача'
    parameter_name = 'user_status'

    def lookups(self, request, model_admin):
        return (
            ('active_in_chat', 'Активний бот + в чаті'),
            ('active_no_chat', 'Активний бот + не в чаті'),
            ('inactive_in_chat', 'Неактивний бот + в чаті'),
            ('inactive_no_chat', 'Неактивний бот + не в чаті'),
            ('never_checked', 'Ніколи не перевірявся'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'active_in_chat':
            return queryset.filter(is_active=True, in_chat=True)
        if self.value() == 'active_no_chat':
            return queryset.filter(is_active=True, in_chat=False)
        if self.value() == 'inactive_in_chat':
            return queryset.filter(is_active=False, in_chat=True)
        if self.value() == 'inactive_no_chat':
            return queryset.filter(is_active=False, in_chat=False)
        if self.value() == 'never_checked':
            return queryset.filter(last_status_check__isnull=True)

@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    change_list_template = 'admin/dashboard/telegramuser/change_list.html'
    
    list_display = ('user_id', 'username_display', 'language', 
                   'referrals_display', 'bot_status', 'chat_status', 
                   'last_check_display', 'join_date')
    list_filter = (UserStatusFilter, HasReferralsFilter, 'language', 'in_chat', 'is_active')
    search_fields = ('user_id', 'username', 'referral_code')
    ordering = ('-join_date',)
    actions = [check_users_status, send_message_to_users]

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('referral-stats/', 
                 self.admin_site.admin_view(self.referral_stats_view),
                 name='referral_stats'),
            path('send-message/',
                 self.admin_site.admin_view(self.send_message_view),
                 name='send_message'),
            path('import-users/', 
                 self.admin_site.admin_view(self.import_users_view),
                 name='import-users')
        ]
        return my_urls + urls

    def username_display(self, obj):
        if obj.username:
            return format_html(
                '<a href="https://t.me/{}" target="_blank">{}</a>',
                obj.username,
                obj.username
            )
        return f'User {obj.user_id}'
    username_display.short_description = 'Username'

    def referrals_display(self, obj):
        count = obj.referrals.count()
        if count > 0:
            return format_html(
                '<span style="color: green;">{}</span> {}',
                count,
                'рефералів' if count != 1 else 'реферал'
            )
        return '0 рефералів'
    referrals_display.short_description = 'Реферали'

    def bot_status(self, obj):
        icon = '✓' if obj.is_active else '✗'
        color = 'green' if obj.is_active else 'red'
        status = 'Активний' if obj.is_active else 'Видалив бота'
        date = f" ({obj.deleted_bot_at.strftime('%d.%m.%Y')})" if obj.deleted_bot_at else ""
        return format_html(
            '<span style="color: {};">{} {}{}</span>', 
            color, icon, status, date
        )
    bot_status.short_description = 'Статус бота'

    def chat_status(self, obj):
        icon = '✓' if obj.in_chat else '✗'
        color = 'green' if obj.in_chat else 'red'
        status = 'В чаті' if obj.in_chat else 'Не в чаті'
        date = f" (вийшов {obj.left_chat_at.strftime('%d.%m.%Y')})" if obj.left_chat_at else ""
        return format_html(
            '<span style="color: {};">{} {}{}</span>', 
            color, icon, status, date
        )
    chat_status.short_description = 'Статус в чаті'

    def last_check_display(self, obj):
        if obj.last_status_check:
            return obj.last_status_check.strftime('%d.%m.%Y %H:%M')
        return 'Не перевірявся'
    last_check_display.short_description = 'Остання перевірка'

    def send_message_view(self, request):
        if 'ids' in request.GET:
            ids = request.GET['ids'].split(',')
            users = TelegramUser.objects.filter(id__in=ids)
        else:
            users = TelegramUser.objects.none()

        if request.method == 'POST':
            form = MessageForm(request.POST)
            if form.is_valid():
                text = form.cleaned_data['message_text']
                photo_url = form.cleaned_data.get('photo_url')
                
                buttons = None
                if form.cleaned_data.get('add_buttons'):
                    button_text = form.cleaned_data.get('button_text')
                    button_url = form.cleaned_data.get('button_url')
                    if button_text and button_url:
                        buttons = {
                            'inline_keyboard': [[{
                                'text': button_text,
                                'url': button_url
                            }]]
                        }

                sender = MessageSender()
                results = asyncio.run(
                    sender.send_bulk_message(list(users), text, photo_url, buttons)
                )
                
                self.message_user(
                    request,
                    f'Повідомлення відправлено: {results["sent"]} успішно, '
                    f'{results["failed"]} помилок, {results["inactive"]} неактивних користувачів'
                )
                return redirect('..')
        else:
            form = MessageForm()

        context = {
            'title': 'Відправка повідомлення',
            'form': form,
            'users_count': users.count(),
            'active_users': users.filter(is_active=True).count(),
            'opts': self.model._meta,
        }
        
        return TemplateResponse(
            request,
            'admin/dashboard/send_message.html',
            context
        )

    def import_users_view(self, request):
        if request.method == 'POST':
            try:
                json_path = r'C:\1\drophelper-bot\data\users.json'
                if not os.path.exists(json_path):
                    raise FileNotFoundError(f"File not found: {json_path}")
                
                from django.core.management import call_command
                call_command('import_users', json_path)
                
                self.message_user(
                    request,
                    'Users successfully imported from users.json',
                    messages.SUCCESS
                )
            except Exception as e:
                self.message_user(
                    request,
                    f'Error importing users: {str(e)}',
                    messages.ERROR
                )
        return redirect('admin:dashboard_telegramuser_changelist')

    def referral_stats_view(self, request):
        total_users = TelegramUser.objects.count()
        users_with_refs = TelegramUser.objects.annotate(
            refs_count=Count('referrals')
        ).filter(refs_count__gt=0)
        
        total_referrals = sum(user.refs_count for user in users_with_refs)
        
        top_referrers = users_with_refs.order_by('-refs_count')[:20]
        for user in top_referrers:
            user.refs_count = user.referrals.count()
        
        ranges = [
            {'min': 0, 'max': 0, 'name': 'Без рефералів'},
            {'min': 1, 'max': 2, 'name': '1-2 реферали'},
            {'min': 3, 'max': 5, 'name': '3-5 рефералів'},
            {'min': 6, 'max': 10, 'name': '6-10 рефералів'},
            {'min': 11, 'max': None, 'name': '11+ рефералів'}
        ]

        referral_ranges = []
        for r in ranges:
            if r['max'] is None:
                count = users_with_refs.filter(refs_count__gte=r['min']).count()
            elif r['min'] == 0:
                count = TelegramUser.objects.annotate(
                    refs_count=Count('referrals')
                ).filter(refs_count=0).count()
            else:
                count = users_with_refs.filter(
                    refs_count__gte=r['min'], 
                    refs_count__lte=r['max']
                ).count()
            
            referral_ranges.append({
                'name': r['name'],
                'count': count,
                'percentage': (count / total_users * 100) if total_users > 0 else 0
            })

        context = {
            'title': 'Статистика рефералів',
            'total_users': total_users,
            'users_with_referrals': users_with_refs.count(),
            'referral_percentage': (users_with_refs.count() / total_users * 100) if total_users > 0 else 0,
            'total_referrals': total_referrals,
            'top_referrers': top_referrers,
            'referral_ranges': referral_ranges,
            'opts': self.model._meta,
        }
        
        return TemplateResponse(
            request,
            'admin/dashboard/referral_stats.html',
            context
        )

@admin.register(Statistics)
class StatisticsAdmin(admin.ModelAdmin):
    list_display = ('date', 'total_bot_users', 'webapp_opens', 
                   'language_distribution', 'chat_members_display')
    ordering = ('-date',)

    def language_distribution(self, obj):
        return format_html(
            'RU: {} | UA: {} | EN: {}',
            obj.ru_users, obj.ua_users, obj.en_users
        )
    language_distribution.short_description = 'Мови'

    def chat_members_display(self, obj):
        total = obj.total_bot_users
        if total > 0:
            percentage = (obj.chat_members * 100) / total
            return format_html(
                '{} з {} ({}%)',
                obj.chat_members, 
                total, 
                round(percentage, 1)
            )
        return '0 з 0 (0%)'
    chat_members_display.short_description = 'Учасники чату'

@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'action_type', 'created_at')
    list_filter = ('action_type', 'created_at')
    search_fields = ('user__username', 'user__user_id')
    ordering = ('-created_at',)

# Налаштування заголовків адмінки
admin.site.site_header = "DropHelper Bot Адміністрування"
admin.site.site_title = "DropHelper Bot"
admin.site.index_title = "Панель управління"