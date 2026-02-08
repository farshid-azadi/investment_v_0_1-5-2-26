from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class LotteryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.lottery'
    label = 'lottery'  # ✅ بسیار مهم برای نام‌گذاری جداول
    verbose_name = _('مدیریت لاتاری و قرعه‌کشی')
