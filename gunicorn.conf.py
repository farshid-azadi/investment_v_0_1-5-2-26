# gunicorn.conf.py
"""
Gunicorn configuration for production.
"""

import multiprocessing

# اتصال
bind = "unix:/run/gunicorn/investment.sock"
# یا برای تست: bind = "127.0.0.1:8000"

# تعداد Worker ها
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"

# Timeout
timeout = 120
graceful_timeout = 30
keepalive = 5

# لاگ‌ها
accesslog = "/var/log/gunicorn/access.log"
errorlog = "/var/log/gunicorn/error.log"
loglevel = "info"

# متغیرهای محیطی
raw_env = [
    "DJANGO_ENV=production",
    "DJANGO_SETTINGS_MODULE=config.settings",
]

# امنیت
limit_request_body = 10485760  # 10MB
daemon = False
preload_app = True
