from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import TelegramUser, UserActivity

@login_required
def dashboard(request):
    today = timezone.now().date()
    
    context = {
        'active_users_count': TelegramUser.objects.filter(is_active=True).count(),
        'new_users_today': TelegramUser.objects.filter(
            first_seen__date=today
        ).count(),
        'deleted_users_today': TelegramUser.objects.filter(
            deleted_at__date=today
        ).count(),
    }
    
    return render(request, 'dashboard/index.html', context)