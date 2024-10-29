from django.db import models
from django.utils import timezone

class TelegramUser(models.Model):
    user_id = models.BigIntegerField(unique=True)
    username = models.CharField(max_length=255, blank=True, null=True)
    language = models.CharField(max_length=10, default='en')
    tokens = models.IntegerField(default=5000)
    referral_code = models.CharField(max_length=50, unique=True, blank=True, null=True)
    referred_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals')
    join_date = models.DateTimeField(default=timezone.now)
    last_webapp_open = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    in_chat = models.BooleanField(default=False)
    chat_join_date = models.DateTimeField(null=True, blank=True)
    last_status_check = models.DateTimeField(null=True, blank=True)
    deleted_bot_at = models.DateTimeField(null=True, blank=True)
    left_chat_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Telegram User"
        verbose_name_plural = "Telegram Users"

    def __str__(self):
        return f"{self.username or self.user_id}"

class Statistics(models.Model):
    date = models.DateField(unique=True, default=timezone.now)
    total_bot_users = models.IntegerField(default=0)
    webapp_opens = models.IntegerField(default=0)
    ru_users = models.IntegerField(default=0)
    ua_users = models.IntegerField(default=0)
    en_users = models.IntegerField(default=0)
    total_spots = models.IntegerField(default=10000)
    used_spots = models.IntegerField(default=0)
    chat_members = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Statistics"
        verbose_name_plural = "Statistics"
        ordering = ['-date']

    def __str__(self):
        return f"Статистика за {self.date}"

class UserActivity(models.Model):
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE)
    action_type = models.CharField(max_length=50)  # 'start', 'webapp_open', 'join_chat', 'leave_chat'
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "User Activity"
        verbose_name_plural = "User Activities"

    def __str__(self):
        return f"{self.user}: {self.action_type} at {self.created_at}"