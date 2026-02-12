# apps/accounts/services/plan_service.py

from decimal import Decimal
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import UserPlan, UserInvestment
from apps.accounts.utils import propagate_volume, distribute_level_commission
from apps.wallet.models import Transaction, Wallet
from apps.core.models import Plan


@transaction.atomic
def purchase_plan(user, plan: Plan, amount: Decimal) -> UserInvestment:
    """
    خرید پلن زمانی که موجودی کاربر کفایت می‌کند.

    1) چک موجودی کیف پول (Wallet.balance)
    2) ثبت تراکنش خروجی (investment)
    3) ساخت UserInvestment
    4) Deactivate کردن UserPlan قبلی و ساخت UserPlan جدید
    5) اجرای کمیسیون سطحی و باینری
    """

    # 0️⃣ قفل کیف پول برای جلوگیری از Race Condition
    wallet = Wallet.objects.select_for_update().get(user=user)

    # 1️⃣ بررسی موجودی
    if wallet.balance < amount:
        raise ValueError("موجودی کیف پول کافی نیست.")

    # 2️⃣ کسر موجودی و ثبت تراکنش
    wallet.balance -= amount
    wallet.save()

    Transaction.objects.create(
        wallet=wallet,
        amount=amount,
        tx_type='investment',  # داخل مدل Transaction این مقدار باید exist داشته باشد
        status='confirmed',
        description=f"Purchase plan: {plan.name}"
    )

    # 3️⃣ غیر فعال کردن پلن فعال قبلی (در صورت وجود)
    UserPlan.objects.filter(
        user=user,
        is_active=True
    ).update(is_active=False, expires_at=timezone.now())

    # 4️⃣ ساخت UserPlan جدید
    user_plan = UserPlan.objects.create(
        user=user,
        plan=plan,
        principal_amount=amount,
        is_active=True
    )

    # 5️⃣ ساخت سرمایه‌گذاری اصلی
    investment = UserInvestment.objects.create(
        user=user,
        plan=plan,
        amount=amount,
        status='active',
        ROI_start_date=timezone.now(),
        expires_at=timezone.now() + plan.duration
    )

    # 6️⃣ پورسانت سطحی
    distribute_level_commission(
        buyer=user,
        plan_price=amount
    )

    # 7️⃣ حجم باینری
    if plan.binary_volume > 0:
        propagate_volume(
            user=user,
            volume=plan.binary_volume
        )

    return investment
