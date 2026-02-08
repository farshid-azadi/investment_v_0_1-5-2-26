from django.apps import AppConfig

class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.accounts'
    label = 'accounts'
    verbose_name = "مدیریت کاربران و شبکه"  # ✅ نام فارسی ماژول

    def ready(self):
        import apps.accounts.signals
