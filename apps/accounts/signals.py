# apps/accounts/signals.py
#17-10-1404 Entirely updated and write Again.!

# apps/accounts/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from decimal import Decimal
import uuid

from .models import PaymentRequest
from apps.investments.models import UserInvestment

User = get_user_model()

@receiver(post_save, sender=User)
def generate_referral_code_after_investment(sender, instance, created, **kwargs):
    """
    تولید کد رفرال فقط بعد از اولین سرمایه‌گذاری موفق
    """
    if not created:  # فقط برای آپدیت‌ها
        # چک کن که آیا کاربر سرمایه‌گذاری فعال داره
        has_active_investment = instance.investments.filter(status='active').exists()
        
        # اگه سرمایه‌گذاری فعال داره اما کد رفرال نداره
        if has_active_investment and not instance.referral_code:
            unique_code = str(uuid.uuid4())[:8].upper()
            
            # اطمینان از یکتا بودن کد
            while User.objects.filter(referral_code=unique_code).exists():
                unique_code = str(uuid.uuid4())[:8].upper()
            
            instance.referral_code = unique_code
            instance.save(update_fields=['referral_code'])


@receiver(post_save, sender=PaymentRequest)
def create_investment_from_approved_payment(sender, instance, created, **kwargs):
    """
    وقتی PaymentRequest به approved تغییر وضعیت داد، Investment ساخته شود
    """
    if not created and instance.status == 'approved' and not instance.related_investment:
        try:
            # اطمینان از وجود مبلغ تأیید شده
            if not instance.verified_amount or instance.verified_amount <= 0:
                print(f"❌ خطا: مبلغ تأیید شده برای payment {instance.id} صفر یا منفی است")
                return

            # ساخت Investment
            investment = UserInvestment.objects.create(
                user=instance.user,
                plan_type=instance.plan.name,  # نام پلن
                amount=instance.verified_amount,
                daily_interest_rate=instance.plan.daily_interest_rate / Decimal('100'),  # ✅ تصحیح شده
                status='active'
            )

            # ربط دادن PaymentRequest به Investment
            instance.related_investment = investment
            instance.save(update_fields=['related_investment'])

            print(f"✅ Investment ساخته شد: {investment.id} برای {instance.user.username}")

        except Exception as e:
            print(f"❌ خطا در ساخت Investment: {e}")
