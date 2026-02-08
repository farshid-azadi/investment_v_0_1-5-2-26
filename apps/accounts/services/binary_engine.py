# apps/accounts/services/binary_engine.py

from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from apps.core.models import MLMSettings
from apps.accounts.models import BinaryCommission
from apps.wallet.models import Transaction, Wallet

@transaction.atomic
def calculate_binary_commission(user):
    """
    محاسبه و پرداخت سود باینری با اعمال قانون Capping (سقف درآمد) و Flushing (سوخت شدن مازاد).
    """
    # 1. دریافت تنظیمات کلی
    settings_mlm = MLMSettings.objects.first()
    default_percent = settings_mlm.binary_percentage if settings_mlm else 10

    # 2. بررسی پلن فعال کاربر
    if not hasattr(user, "active_plan") or not user.active_plan.is_active:
        return Decimal("0")

    plan = user.active_plan.plan
    
    # تعیین درصد سود (اولویت با پلن، اگر نبود تنظیمات کلی)
    percentage = plan.binary_percentage if plan.binary_percentage > 0 else default_percent
    
    # تعیین سقف درآمد روزانه (Capping)
    daily_cap = plan.daily_binary_cap

    # 3. محاسبه حجم تعادل (سمت ضعیف)
    left = user.left_volume
    right = user.right_volume
    matched_volume = min(left, right)

    if matched_volume <= 0:
        return Decimal("0")

    # 4. محاسبه سود خام (بدون در نظر گرفتن سقف)
    raw_commission = matched_volume * (percentage / Decimal("100"))

    # 5. اعمال قانون Capping (سقف)
    if raw_commission > daily_cap:
        paid_amount = daily_cap
        flushed_amount = raw_commission - daily_cap  # مبلغی که می‌سوزد و به سیستم می‌رسد
    else:
        paid_amount = raw_commission
        flushed_amount = Decimal("0")

    # 6. ثبت رکورد در دیتابیس (Log دقیق)
    BinaryCommission.objects.create(
        user=user,
        matched_volume=matched_volume,
        percentage=percentage,
        calc_amount=raw_commission,    # سود محاسبه شده
        paid_amount=paid_amount,       # سود پرداخت شده
        flushed_amount=flushed_amount  # سود سوخت شده
    )

    # 7. کسر حجم‌ها از چپ و راست
    user.left_volume -= matched_volume
    user.right_volume -= matched_volume
    
    # آپدیت آمار کلی کاربر
    user.total_commission_earned += paid_amount
    user.save()

    # 8. واریز پول به کیف پول (Wallet) با تقسیم 50/50 (اگر قانونش باشد) یا واریز کامل
    # فرض بر واریز نقدی به Balance است. اگر تقسیم 50/50 دارید اینجا تغییر می‌کند.
    wallet, _ = Wallet.objects.get_or_create(user=user)
    wallet.balance += paid_amount
    wallet.save()

    # 9. ثبت تراکنش مالی
    Transaction.objects.create(
        wallet=wallet,
        amount=paid_amount,
        transaction_type='binary_bonus_cash',
        status='confirmed',
        description=f"Binary Commission. Matched: {matched_volume}, Flushed: {flushed_amount}",
        meta_data={
            "raw_commission": str(raw_commission),
            "flushed": str(flushed_amount),
            "cap_limit": str(daily_cap)
        }
    )

    return paid_amount
