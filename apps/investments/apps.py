from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class InvestmentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.investments'
    verbose_name = _('Investment Management')
    label = 'investments'  # مهم برای جلوگیری از تداخل نام‌ها
