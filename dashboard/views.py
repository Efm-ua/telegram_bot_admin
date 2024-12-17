from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import TelegramUser, Statistics
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q

@login_required
def dashboard(request):
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    week_ago = today - timedelta(days=7)

    # Активні користувачі (ті, хто не видалив бота)
    active_users = TelegramUser.objects.filter(is_active=True).count()

    # Нові користувачі за сьогодні
    new_users_today = TelegramUser.objects.filter(
        join_date__date=today
    ).count()

    # Видалені користувачі за сьогодні
    deleted_users_today = TelegramUser.objects.filter(
        deleted_bot_at__date=today
    ).count()

    # Активність за останні 7 днів
    daily_activity = []
    for i in range(7):
        day = today - timedelta(days=i)
        new_users = TelegramUser.objects.filter(join_date__date=day).count()
        deleted_users = TelegramUser.objects.filter(deleted_bot_at__date=day).count()
        daily_activity.append({
            'date': day,
            'new_users': new_users,
            'deleted_users': deleted_users,
        })

    # Статистика по мовах
    language_stats = TelegramUser.objects.values('language').annotate(
        count=Count('id')
    ).order_by('-count')

    # Статистика по чату
    chat_stats = {
        'in_chat': TelegramUser.objects.filter(in_chat=True).count(),
        'not_in_chat': TelegramUser.objects.filter(in_chat=False).count(),
    }

    # Статистика рефералів
    referral_stats = TelegramUser.objects.filter(referrals__isnull=False).annotate(
        refs_count=Count('referrals')
    ).order_by('-refs_count')[:5]

    context = {
        'active_users': active_users,
        'new_users_today': new_users_today,
        'deleted_users_today': deleted_users_today,
        'daily_activity': daily_activity,
        'language_stats': language_stats,
        'chat_stats': chat_stats,
        'referral_stats': referral_stats,
        'total_users': TelegramUser.objects.count(),
    }
    
    return render(request, 'dashboard/index.html', context)