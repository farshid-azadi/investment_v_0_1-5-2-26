"""
Wallet Signals - سیگنال‌های مرتبط با Wallet
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from apps.wallet.models import Wallet


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_wallet(sender, instance, created, **kwargs):
    """
    ایجاد خودکار Wallet برای کاربر جدید
    
    این سیگنال بلافاصله پس از ایجاد یک کاربر جدید،
    یک کیف پول خالی برای او ایجاد می‌کند.
    """
    if created:
        Wallet.objects.create(user=instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_wallet(sender, instance, **kwargs):
    """
    ذخیره Wallet همزمان با User
    
    اطمینان از اینکه در صورت وجود Wallet،
    همزمان با User ذخیره شود.
    """
    if hasattr(instance, 'wallet'):
        instance.wallet.save()
