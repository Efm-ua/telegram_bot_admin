from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from django.urls import reverse, path
from django.template.response import TemplateResponse
from .models import TelegramUser, Statistics, UserActivity

@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    change_list_template = 'admin/dashboard/telegramuser/change_list.html'
    
    list_display = ('user_id', 'username_display', 'language', 
                   'referrals_display', 'chat_status', 'join_date')
    list_filter = ('in_chat', 'language', 'is_active')
    search_fields = ('user_id', 'username', 'referral_code')
    ordering = ('-join_date',)

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('referral-stats/', 
                 self.admin_site.admin_view(self.referral_stats_view),
                 name='referral_stats'),
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
        return f"{count} {'рефералів' if count != 1 else 'реферал'}"
    referrals_display.short_description = 'Реферали'

    def chat_status(self, obj):
        icon = '✓' if obj.in_chat else '✗'
        color = 'green' if obj.in_chat else 'red'
        status = 'У чаті' if obj.in_chat else 'Не в чаті'
        return format_html(
            '<span style="color: {};">{} {}</span>', 
            color, icon, status
        )
    chat_status.short_description = 'Статус у чаті'

    def referral_stats_view(self, request):
        # Загальна статистика
        total_users = TelegramUser.objects.count()
        users_with_refs = TelegramUser.objects.annotate(
            refs_count=Count('referrals')
        ).filter(refs_count__gt=0)
        
        total_referrals = sum(user.refs_count for user in users_with_refs)
        
        # Топ рефоводів
        top_referrers = users_with_refs.order_by('-refs_count')[:20]
        for user in top_referrers:
            user.refs_count = user.referrals.count()
        
        # Розподіл за діапазонами
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

# Налаштування заголовків адмінки
admin.site.site_header = "DropHelper Bot Адміністрування"
admin.site.site_title = "DropHelper Bot"
admin.site.index_title = "Панель управління"