"""
انتخاب‌گر خودکار تنظیمات بر اساس متغیر محیطی DJANGO_ENV

استفاده:
- توسعه (پیش‌فرض): DJANGO_ENV=development یا عدم تنظیم متغیر
- پروداکشن: DJANGO_ENV=production

تغییرات نسخه جدید:
- حذف print statements در production برای امنیت بهتر
- اضافه کردن validation برای مقادیر معتبر
"""

import os
import sys

# خواندن متغیر محیطی (پیش‌فرض: development)
DJANGO_ENV = os.environ.get('DJANGO_ENV', 'development').lower().strip()

# لیست محیط‌های معتبر
VALID_ENVIRONMENTS = ['development', 'production']

# اعتبارسنجی محیط
if DJANGO_ENV not in VALID_ENVIRONMENTS:
    print(
        f"⚠️  هشدار: محیط '{DJANGO_ENV}' نامعتبر است.\n"
        f"   محیط‌های معتبر: {', '.join(VALID_ENVIRONMENTS)}\n"
        f"   بازگشت به حالت 'development'...\n",
        file=sys.stderr
    )
    DJANGO_ENV = 'development'

# بارگذاری تنظیمات مناسب
if DJANGO_ENV == 'production':
    from .production import *
    # در production از print استفاده نمی‌کنیم (امنیت)
elif DJANGO_ENV == 'development':
    from .development import *
    # فقط در development پیام نمایش داده می‌شود
    if os.environ.get('DJANGO_SETTINGS_DEBUG', 'true').lower() == 'true':
        print("🔧 محیط: DEVELOPMENT")
