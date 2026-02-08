# config/wsgi.py
"""
WSGI config for investment project.

در محیط پروداکشن، متغیر DJANGO_ENV باید روی 'production' تنظیم شود.
این کار می‌تواند در فایل سرویس systemd یا در Gunicorn انجام شود.
"""

import os
from django.core.wsgi import get_wsgi_application

# تنظیم مسیر تنظیمات
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# در صورت نیاز، می‌توانید اینجا DJANGO_ENV را هم تنظیم کنید
# اما بهتر است از خارج (systemd یا Gunicorn) تنظیم شود
# os.environ.setdefault('DJANGO_ENV', 'production')

application = get_wsgi_application()
