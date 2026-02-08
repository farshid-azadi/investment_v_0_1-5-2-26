# apps/accounts/signals.py

import random
import string
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.investments.models import UserInvestment  # ✅ مسیر صحیح
from .models import User
import logging

logger = logging.getLogger(__name__)


def generate_unique_referral_code():
    """
    تولید کد معرف 8 کاراکتری یونیک (حروف بزرگ + اعداد)
    """
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        if not User.objects.filter(referral_code=code).exists():
            return code


@receiver(post_save, sender=UserInvestment)
def handle_new_investment(sender, instance, created, **kwargs):
    """
    سیگنال هنگام خرید پلن:
    1️⃣ تولید کد معرف (فقط اولین خرید)
    2️⃣ فراخوانی Taskهای مالی (فقط برای وضعیت active)
    """
    
    # -------------------------------------------------------------------------
    # 1️⃣ تولید کد معرف (فقط در اولین خرید فعال)
    # -------------------------------------------------------------------------
    if created and instance.status == 'active':
        user = instance.user
        
        # اگر کاربر کد معرف نداره، تولید کن
        if not user.referral_code:
            user.referral_code = generate_unique_referral_code()
            user.save(update_fields=['referral_code'])
            logger.info(f"✅ کد معرف تولید شد: {user.referral_code} برای {user.username}")

    # -------------------------------------------------------------------------
    # 2️⃣ فراخوانی Taskها (فقط برای وضعیت active)
    # -------------------------------------------------------------------------
    if created and instance.status == 'active':
        # ✅ استفاده صحیح از فیلد amount
        plan_price = float(instance.amount)  
        buyer_id = instance.user.id
        
        # ✅ وارد کردن Taskها
        from apps.accounts.tasks import (
            task_distribute_level_commission,
            task_propagate_volume
        )
        
        try:
            # 🔹 Task 1: پرداخت کمیسیون سطحی (همزمان)
            task_distribute_level_commission(buyer_id, plan_price)
            logger.info(f"✅ Task کمیسیون سطحی برای {buyer_id} اجرا شد.")
        
        except Exception as e:
            logger.error(f"❌ خطا در Task کمیسیون سطحی: {e}")
        
        try:
            # 🔹 Task 2: انتشار حجم (همزمان)
            task_propagate_volume(buyer_id, plan_price)
            logger.info(f"✅ Task انتشار حجم برای {buyer_id} اجرا شد.")
        
        except Exception as e:
            logger.error(f"❌ خطا در Task انتشار حجم: {e}")
