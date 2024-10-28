"""
ASGI config for telegram_admin project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'telegram_admin.settings')

application = get_asgi_application()