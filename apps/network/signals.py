from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from decimal import Decimal
from apps.investments.models import UserInvestment
from apps.wallet.models import Transaction, Wallet

@receiver(post_save, sender=UserInvestment)
def distribute_referral_commission(sender, instance, created, **kwargs):
    """
    وقتی سرمایه‌گذاری جدیدی ایجاد می‌شود، به معرف‌ها بر اساس سطوح تعریف شده پاداش می‌دهد.
    """
    if created:
        user = instance.user
        amount = instance.amount
        
        # خواندن سطوح از تنظیمات (پیش‌فرض اگر نبود: [10, 5, 3])
        levels = getattr(settings, 'MLM_LEVELS', [10, 5, 3])
        
        current_referrer = user.referrer
        
        # حلقه روی سطوح (Level 1, Level 2, ...)
        for level_percent in levels:
            if not current_referrer:
                break # اگر معرفی وجود نداشت، حلقه متوقف می‌شود

            # محاسبه پاداش
            commission = (amount * Decimal(level_percent)) / 100
            
            # واریز به کیف پول معرف
            # نکته: استفاده از select_for_update برای جلوگیری از Race Condition در پروژه‌های بزرگ توصیه می‌شود
            wallet, _ = Wallet.objects.get_or_create(user=current_referrer)
            wallet.balance += commission
            wallet.save()

            # ثبت تراکنش
            Transaction.objects.create(
                wallet=wallet,
                amount=commission,
                transaction_type='referral_reward',
                status='confirmed',
                description=f'Referral Commission from {user.username} (Level {levels.index(level_percent) + 1})'
            )

            # حرکت به سطح بالاتر (معرفِ معرف)
            current_referrer = current_referrer.referrer
