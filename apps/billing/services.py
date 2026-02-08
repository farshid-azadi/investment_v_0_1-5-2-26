# apps/billing/services.py (یا هر جایی که محاسبه باینری انجام می‌شود)
from decimal import Decimal
from django.db.models import Sum
from apps.accounts.models import BurnedIncome, BinaryCommission
from apps.wallet.models import Transaction

def calculate_and_pay_binary(user):
    """
    محاسبه باینری با اعمال قوانین جدید:
    1. سقف روزانه = کل سرمایه فعال کاربر
    2. سقف کل (Total Cap) = درصد تعیین شده در پلن (مثلا 250٪)
    """
    
    # 1. محاسبه حجم‌ها (ساده شده)
    left = user.left_volume
    right = user.right_volume
    weak_leg_vol = min(left, right)
    
    if weak_leg_vol <= 0:
        return

    # درصد باینری (فرض کنیم 10 درصد ثابت است یا از تنظیمات می‌آید)
    BINARY_PERCENT = Decimal('0.10')
    raw_commission = weak_leg_vol * BINARY_PERCENT

    # 2. دریافت مجموع سرمایه‌گذاری فعال کاربر (برای سقف روزانه)
    # فرض: سرمایه‌هایی که هنوز status='active' هستند
    active_investments = user.investments.filter(status='active')
    total_active_invest_amount = active_investments.aggregate(s=Sum('amount'))['s'] or Decimal('0')

    if total_active_invest_amount == 0:
        # کاربری که سرمایه فعال ندارد، سودی هم نمی‌گیرد (همه اش سوخت می‌شود یا اصلا محاسبه نمی‌شود)
        # طبق خواسته شما: تا پلن نخرد کد ندارد، پس احتمالا اینجا نمی‌رسد.
        # اما محض اطمینان، اگر سرمایه ندارد، سقف 0 است.
        daily_cap = 0
    else:
        daily_cap = total_active_invest_amount

    # 3. اعمال سقف روزانه (Daily Cap)
    payable_amount = raw_commission
    burned_daily = Decimal('0')

    if payable_amount > daily_cap:
        burned_daily = payable_amount - daily_cap
        payable_amount = daily_cap  # سقف اعمال شد
        
        # ثبت لاگ سوخت شده
        BurnedIncome.objects.create(
            user=user,
            amount=burned_daily,
            reason='daily_cap',
            description=f'Raw: {raw_commission}, Cap: {daily_cap}'
        )

    # 4. اعمال سقف کل پلن (Total Plan Cap - 250%)
    # باید چک کنیم این کاربر تا الان چقدر از سیستم گرفته است.
    # نکته: چون کاربر ممکن است چند پلن داشته باشد، معمولا سقف را روی "مجموع سرمایه فعال" حساب می‌کنیم.
    
    # پیدا کردن میانگین یا کمترین درصد کپ در بین پلن‌های فعال (یا پلن اصلی)
    # فرض: از پلنی استفاده می‌کنیم که بیشترین درصد کپ را دارد تا به نفع کاربر باشد
    max_cap_percent = 250 # پیش فرض
    if active_investments.exists():
        max_cap_percent = active_investments.first().plan.max_total_return_percent

    max_allowed_earning = total_active_invest_amount * (max_cap_percent / Decimal(100))
    
    # کل درآمد کسب شده تا الان (شامل همین مبلغ جدید که هنوز واریز نشده)
    previous_earnings = user.total_commission_earned # فرض: این فیلد در مدل User آپدیت می‌شود
    
    potential_total = previous_earnings + payable_amount
    
    burned_total_cap = Decimal('0')

    if potential_total > max_allowed_earning:
        # چقدر جا دارد؟
        remaining_room = max_allowed_earning - previous_earnings
        if remaining_room < 0: remaining_room = 0
        
        original_payable = payable_amount
        payable_amount = remaining_room # فقط اندازه جای خالی واریز کن
        
        burned_total_cap = original_payable - payable_amount
        
        # ثبت لاگ سوخت سقف کلی
        if burned_total_cap > 0:
            BurnedIncome.objects.create(
                user=user,
                amount=burned_total_cap,
                reason='total_cap',
                description=f'Max Allowed: {max_allowed_earning}, Prev: {previous_earnings}'
            )
            
        # غیرفعال کردن پلن‌ها اگر پر شد؟
        # معمولا در این نقطه اگر payable_amount صفر شود، یعنی سقف پر شده.
        # می‌توانید لاجیک غیرفعال کردن سرمایه‌گذاری را اینجا بگذارید.

    # 5. واریز نهایی و کسر حجم
    if payable_amount > 0:
        # واریز به کیف پول
        Transaction.objects.create(wallet=user.wallet, amount=payable_amount, transaction_type='binary_commission')
        user.wallet.balance += payable_amount
        user.wallet.save()
        
        # ثبت رکورد باینری
        BinaryCommission.objects.create(user=user, paid_amount=payable_amount, matched_volume=weak_leg_vol)
        
        # آپدیت مجموع درآمد کاربر
        user.total_commission_earned += payable_amount
        user.save()

    # کسر حجم‌ها (Flush)
    user.left_volume -= weak_leg_vol
    user.right_volume -= weak_leg_vol
    user.save()

    print(f"Binary Processed for {user.username}: Paid={payable_amount}, BurnedDaily={burned_daily}, BurnedTotal={burned_total_cap}")
