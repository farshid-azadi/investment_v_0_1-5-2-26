from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from .models import UserInvestment
from apps.wallet.models import Transaction, Wallet

def process_daily_profits():
    """
    این تابع تمام سرمایه‌گذاری‌های فعال را بررسی می‌کند،
    سود روزانه را محاسبه و واریز می‌کند و
    اگر زمان پلن تمام شده باشد، وضعیت را به تکمیل شده تغییر می‌دهد.
    """
    today = timezone.now().date()
    
    # دریافت سرمایه‌گذاری‌های فعال
    active_investments = UserInvestment.objects.filter(status='active')
    
    reports = {
        'processed_count': 0,
        'total_profit_paid': Decimal('0.00'),
        'completed_plans': 0,
        'errors': []
    }

    print(f"--- شروع پردازش سود روزانه برای {len(active_investments)} سرمایه‌گذاری فعال ---")

    for investment in active_investments:
        try:
            with transaction.atomic():
                # 1. محاسبه سود روزانه
                # فرمول: مبلغ سرمایه * (درصد سود روزانه / 100)
                daily_profit = investment.amount * (investment.daily_interest_rate / Decimal('100.00'))
                
                # جلوگیری از اعداد اعشاری خیلی خرد
                daily_profit = daily_profit.quantize(Decimal('0.0001'))

                # 2. واریز به کیف پول کاربر
                wallet = Wallet.objects.select_for_update().get(user=investment.user)
                wallet.balance += daily_profit
                wallet.save()

                # 3. ثبت تراکنش سود
                Transaction.objects.create(
                    wallet=wallet,
                    amount=daily_profit,
                    transaction_type='daily_profit',  # نوع تراکنش سود روزانه
                    status='confirmed',
                    description=f"سود روزانه پلن {investment.plan_type} (ID: {investment.id})"
                )

                # 4. آپدیت آمار سرمایه‌گذاری
                investment.total_profit_earned += daily_profit
                reports['total_profit_paid'] += daily_profit
                
                # 5. بررسی پایان مهلت سرمایه‌گذاری
                # محاسبه تاریخ پایان: تاریخ شروع + تعداد روزهای پلن
                # اگر مدل شما فیلد duration_days ندارد، باید آن را از پلن بگیرید یا فرض کنیم در مدل ذخیره شده
                # در اینجا فرض می‌کنیم duration_days در مدل UserInvestment کپی شده است (طبق کدهای قبلی)
                # اگر نیست، باید آن را اضافه کنیم. فعلاً فرض می‌کنیم هست.
                
                end_date = investment.created_at.date() + timezone.timedelta(days=investment.duration_days)
                
                if today >= end_date:
                    investment.status = 'completed'
                    reports['completed_plans'] += 1
                    
                    # === بخش اختیاری: بازگشت اصل سرمایه ===
                    # اگر می‌خواهید اصل پول بعد از پایان دوره برگردد، کد زیر را فعال کنید:
                    
                    wallet.balance += investment.amount
                    wallet.save()
                    Transaction.objects.create(
                        wallet=wallet,
                        amount=investment.amount,
                        transaction_type='principal_return',
                        status='confirmed',
                        description=f"بازگشت اصل سرمایه پلن {investment.plan_type} (پایان دوره)"
                    )
                    print(f"Plan Completed for User {investment.user.username}. Principal Returned.")
                    # ========================================

                investment.save()
                reports['processed_count'] += 1

        except Exception as e:
            error_msg = f"Error processing investment ID {investment.id}: {str(e)}"
            reports['errors'].append(error_msg)
            print(error_msg)

    return reports
