# apps/network/services.py

from decimal import Decimal
from django.db import transaction
from django.db.models import F
from apps.investments.models import ReferralLevel, UserInvestment
from apps.wallet.models import Transaction, Wallet
from apps.accounts.models import User

# تنظیمات ثابت
BINARY_COMMISSION_RATE = Decimal('0.10')  # 10% سود باینری
MAX_BINARY_CAP_MULTIPLIER = 3  # سقف درآمد باینری (۳ برابر سرمایه)

def distribute_direct_reward(investor, amount):
    """
    محاسبه پاداش معرف مستقیم (Direct Bonus)
    قانون: ۵۰٪ نقد (Wallet) و ۵۰٪ افزایش سرمایه (Reinvest)
    """
    referrer = investor.referrer
    if not referrer:
        return

    # دریافت درصد سطح ۱
    try:
        level_config = ReferralLevel.objects.get(level=1)
        percentage = level_config.commission_percentage
    except ReferralLevel.DoesNotExist:
        percentage = Decimal('5.0') # پیش‌فرض ۵ درصد

    total_commission = amount * (percentage / 100)
    
    # تقسیم ۵۰/۵۰
    cash_part = total_commission / 2
    reinvest_part = total_commission / 2

    print(f"--- Processing Direct Reward for {referrer.username}: Total {total_commission} ---")

    try:
        with transaction.atomic():
            # 1. واریز بخش نقدی به کیف پول
            wallet = Wallet.objects.select_for_update().get(user=referrer)
            wallet.balance += cash_part
            wallet.save()

            Transaction.objects.create(
                wallet=wallet,
                transaction_type='referral_bonus_cash',
                amount=cash_part,
                status='confirmed',
                description=f'Direct Bonus (Cash Part) from user {investor.username}'
            )

            # 2. واریز بخش سرمایه‌گذاری (Reinvest)
            _apply_reinvest(referrer, reinvest_part, 'referral_bonus_reinvest', f'Direct Bonus (Reinvest Part) from {investor.username}')

    except Exception as e:
        print(f"Error distributing direct reward to {referrer.username}: {e}")


def update_binary_volumes(user, amount):
    """
    آپدیت حجم فروش باینری به سمت بالا
    """
    current_user = user
    while current_user.binary_parent:
        parent = current_user.binary_parent
        position = current_user.binary_position

        if position == 'left':
            User.objects.filter(pk=parent.pk).update(left_volume=F('left_volume') + amount)
        elif position == 'right':
            User.objects.filter(pk=parent.pk).update(right_volume=F('right_volume') + amount)

        current_user = parent


def calculate_binary_commission_logic():
    """
    محاسبه سود باینری (اجرا توسط Task روزانه)
    قانون: ۱۰٪ از پای ضعیف -> ۵۰٪ نقد، ۵۰٪ ری‌اینسوت
    """
    print("--- Starting Binary Commission Calculation ---")
    
    # کاربرانی که در هر دو سمت فروش دارند
    users = User.objects.filter(left_volume__gt=0, right_volume__gt=0)

    for user in users:
        with transaction.atomic():
            left = user.left_volume
            right = user.right_volume
            
            # تعیین پای ضعیف
            pay_leg_volume = min(left, right)
            
            if pay_leg_volume <= 0:
                continue

            # محاسبه پاداش خام (۱۰ درصد)
            raw_commission = pay_leg_volume * BINARY_COMMISSION_RATE
            
            # اعمال سقف درآمد (Flash Out)
            # سقف درآمد = ۳ برابر کل سرمایه فعال کاربر
            total_active_capital = sum(inv.active_capital for inv in user.investments.filter(status='active'))
            daily_cap = total_active_capital * MAX_BINARY_CAP_MULTIPLIER
            
            final_commission = raw_commission
            if raw_commission > daily_cap:
                final_commission = daily_cap
                # مابقی فلش می‌شود

            # تقسیم ۵۰/۵۰
            cash_part = final_commission / 2
            reinvest_part = final_commission / 2

            # 1. واریز نقدی
            wallet = Wallet.objects.select_for_update().get(user=user)
            wallet.balance += cash_part
            wallet.save()

            Transaction.objects.create(
                wallet=wallet,
                amount=cash_part,
                transaction_type='binary_bonus_cash',
                status='confirmed',
                description=f"Binary Bonus (Cash) - Matched: {pay_leg_volume}"
            )

            # 2. واریز سرمایه‌گذاری
            _apply_reinvest(user, reinvest_part, 'binary_bonus_reinvest', "Binary Bonus (Reinvest)")

            # کسر حجم‌ها (Flush)
            user.left_volume -= pay_leg_volume
            user.right_volume -= pay_leg_volume
            user.save()
            
            print(f"Binary processed for {user.username}: {final_commission} paid.")


def _apply_reinvest(user, amount, txn_type, desc):
    """
    تابع کمکی برای اضافه کردن مبلغ به active_capital آخرین سرمایه‌گذاری فعال
    """
    # پیدا کردن آخرین سرمایه‌گذاری فعال
    active_inv = UserInvestment.objects.filter(user=user, status='active').order_by('-created_at').first()

    if active_inv:
        active_inv.reinvested_amount += amount
        active_inv.save()

        # ثبت تراکنش صرفا جهت نمایش در تاریخچه (چون پولی به بالانس نقد اضافه نشده)
        # اما برای شفافیت بهتر است ثبت شود که این پول کجا رفت
        Transaction.objects.create(
            wallet=user.wallet,
            amount=amount,
            transaction_type=txn_type,
            status='confirmed',
            description=f"{desc} -> Added to Plan ID {active_inv.id}"
        )
    else:
        # اگر سرمایه‌گذاری فعال نداشت، ناچاراً به کیف پول نقد واریز می‌کنیم
        user.wallet.balance += amount
        user.wallet.save()
        Transaction.objects.create(
            wallet=user.wallet,
            amount=amount,
            transaction_type=txn_type.replace('reinvest', 'cash'), # تغییر نوع به نقد
            status='confirmed',
            description=f"{desc} (No active plan found - Converted to Cash)"
        )
