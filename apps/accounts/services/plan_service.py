# apps/accounts/services/plan_service.py

from django.db import transaction
from django.utils import timezone
from apps.core.models import Plan
from apps.accounts.models import UserPlan, UserInvestment
from apps.accounts.utils import propagate_volume, distribute_level_commission
from apps.wallet.models import Transaction, Wallet # ایمپورت مدل‌های کیف پول


@transaction.atomic
def purchase_plan(user, plan):
    """
    نقطه طلایی پول‌ساز سیستم
    """

    # 1️⃣ بررسی پلن فعال قبلی
    UserPlan.objects.filter(
        user=user,
        is_active=True
    ).update(is_active=False)

    # 2️⃣ فعال کردن پلن جدید
    user_plan = UserPlan.objects.create(
        user=user,
        plan=plan,
        is_active=True
    )

    # 3️⃣ Level / Unilevel Commission
    distribute_level_commission(
        buyer=user,
        plan_price=plan.price
    )

    # 4️⃣ Binary volume injection
    if plan.binary_volume > 0:
        propagate_volume(
            user=user,
            volume=plan.binary_volume
        )

    return user_plan
def purchase_plan(user, plan, amount):
    # 1. دریافت کیف پول
    wallet = Wallet.objects.select_for_update().get(user=user)

    # 2. چک کردن موجودی
    if wallet.balance < amount:
        raise ValueError("موجودی کافی نیست.")

    # 3. کسر موجودی
    wallet.balance -= amount
    wallet.save()

    # 4. ثبت تراکنش (این همان چیزی است که الان ندارید)
    Transaction.objects.create(
        wallet=wallet,
        amount=amount,
        transaction_type='investment', # نوع تراکنش خرید
        status='confirmed',
        description=f"Purchase plan: {plan.name}"
    )

    # 5. ایجاد سرمایه‌گذاری
    investment = UserInvestment.objects.create(
        user=user,
        plan=plan,
        amount=amount,
        status='active'
    )
    
    return investment
