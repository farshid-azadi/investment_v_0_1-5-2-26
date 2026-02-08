"""
Wallet App Configuration
"""
from django.apps import AppConfig


class WalletConfig(AppConfig):
    """تنظیمات اپلیکیشن Wallet"""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.wallet'
    verbose_name = 'کیف پول'
    
    def ready(self):
        """فعال‌سازی سیگنال‌ها هنگام آماده شدن اپلیکیشن"""
        import apps.wallet.signals  # noqa
