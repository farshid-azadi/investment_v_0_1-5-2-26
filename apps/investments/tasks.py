# apps/investments/tasks.py

from celery import shared_task
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from .models import UserInvestment
from apps.wallet.models import Wallet, Transaction
from apps.network.services import calculate_binary_commission_logic

@shared_task
def process_daily_profits():
    """
    1. محاسبه و واریز سود روزانه (ROI) بر اساس سرمایه مرکب.
    2. اجرای محاسبه سود باینری (اختیاری، اگر می‌خواهید با هم اجرا شوند).
    """
    print(f"Executing Daily Profit Task at {timezone.now()}")
    
    # تاریخ فعلی برای چک کردن انقضای پلن
    now = timezone.now()
    
    # فقط سرمایه‌گذاری‌هایی که فعال هستند و تاریخ پایانشان نرسیده
    active_investments = UserInvestment.objects.filter(
        status='active', 
        end_date__gt=now
    )

    count = 0
    
    for investment in active_investments:
        try:
            with transaction.atomic():
                # فرمول جدید: سود بر اساس Active Capital (شامل Reinvest)
                # Active Capital = Initial Amount + Reinvested Amount
                current_capital = investment.active_capital
                daily_rate = investment.daily_interest_rate
                
                daily_profit = (current_capital * daily_rate) / 100
                
                if daily_profit <= 0:
                    continue

                # واریز سود روزانه (ROI) -> 100% نقد طبق سناریو
                wallet = Wallet.objects.select_for_update().get(user=investment.user)
                wallet.balance += daily_profit
                wallet.save()

                # ثبت تراکنش
                Transaction.objects.create(
                    wallet=wallet,
                    amount=daily_profit,
                    transaction_type='daily_profit',
                    status='confirmed',
                    description=f"Daily ROI on Capital: {current_capital} (Plan: {investment.plan_type})"
                )

                # آپدیت مجموع سود دریافتی
                investment.total_profit_earned += daily_profit
                investment.save()
                
                count += 1

        except Exception as e:
            print(f"Error processing investment ID {investment.id}: {e}")

    # پس از واریز سودها، می‌توانید سود باینری را هم محاسبه کنید (یا در تسک جداگانه)
    # calculate_binary_commission_logic()

    return f"Success: Processed profits for {count} investments."

@shared_task
def run_binary_calculation():
    """
    تسک جداگانه برای محاسبه باینری در پایان روز
    """
    calculate_binary_commission_logic()
    return "Binary Calculation Completed."
