# apps/accounts/services/roi_service.py

from django.db.models import F
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from apps.accounts.models import UserPlan, ROIHistory
from apps.wallet.models import Wallet, Transaction

@transaction.atomic
def process_daily_roi():
    """
    اجرای سود روزانه با قابلیت چک کردن روزهای مجاز هفته.
    """
    # 1. به دست آوردن روز جاری هفته
    # در پایتون: Monday=0, Tuesday=1, ... Saturday=5, Sunday=6
    today_index = timezone.now().weekday()
    
    # نگاشت ایندکس پایتون به فیلدهای مدل
    day_mapping = {
        0: 'pay_on_monday',
        1: 'pay_on_tuesday',
        2: 'pay_on_wednesday',
        3: 'pay_on_thursday',
        4: 'pay_on_friday',
        5: 'pay_on_saturday',
        6: 'pay_on_sunday',
    }
    
    # نام فیلدی که باید چک کنیم (مثلا pay_on_sunday)
    current_day_field = day_mapping[today_index]

    # دریافت پلن‌های فعال
    active_plans = UserPlan.objects.filter(
        is_active=True,
        expires_at__gt=timezone.now()
    ).select_related('user', 'plan')

    count = 0
    skipped_count = 0

    for user_plan in active_plans:
        user = user_plan.user
        plan = user_plan.plan

        # --- اصلاحیه جدید: بررسی روز مجاز ---
        # مقدار فیلد مربوط به امروز را از پلن می‌خوانیم
        # مثلا اگر امروز شنبه است، مقدار plan.pay_on_saturday را چک می‌کند
        is_payment_day = getattr(plan, current_day_field, True)

        if not is_payment_day:
            # اگر امروز روز پرداخت این پلن نیست، رد کن
            skipped_count += 1
            continue
        # ------------------------------------

        if plan.roi_percent <= 0:
            continue

        # اصلاحیه مهم قبلی: استفاده از principal_amount (سرمایه واقعی کاربر)
        # اگر principal_amount صفر بود (کاربر قدیمی)، از min_price استفاده کن
        base_amount = user_plan.principal_amount if user_plan.principal_amount > 0 else plan.min_price
        
        roi_amount = base_amount * (plan.roi_percent / Decimal("100"))

        if roi_amount > 0:
            # 1. واریز به ولت
            wallet, _ = Wallet.objects.get_or_create(user=user)
            # استفاده از F برای جلوگیری از Race Condition
            wallet.balance = F('balance') + roi_amount
            wallet.save()
            
            # 2. ثبت تراکنش
            Transaction.objects.create(
                wallet=wallet,
                amount=roi_amount,
                tx_type="roi_profit",
                status="confirmed",
                description=f"Daily ROI for {plan.name} (Plan ID: {user_plan.id})"
            )

            # 3. ثبت تاریخچه ROI
            ROIHistory.objects.create(
                user=user,
                plan=plan,
                amount=roi_amount,
                percent=plan.roi_percent
            )
            count += 1

    print(f"✅ انجام شد. {count} واریز انجام شد. {skipped_count} پلن به دلیل تعطیلی روز رد شدند.")
    return count
