"""
WSGI config for telegram_admin project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'telegram_admin.settings')

application = get_wsgi_application()