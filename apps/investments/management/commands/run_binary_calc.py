# apps/network/management/commands/run_binary_calc.py

from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
from apps.accounts.models import User
from apps.wallet.models import Wallet, Transaction
from apps.investments.models import UserInvestment

class Command(BaseCommand):
    help = 'محاسبه سود باینری (تعادل) و اعمال سقف درآمد'

    def handle(self, *args, **options):
        self.stdout.write("⚖️ شروع محاسبه سود باینری...")
        
        # درصد سود باینری (مثلاً 10 درصد از پای کمتر) - بهتر است از دیتابیس خوانده شود
        BINARY_PERCENT = Decimal('0.10') 

        users = User.objects.filter(left_volume__gt=0, right_volume__gt=0) # فقط کسانی که در هر دو طرف فروش دارند
        
        count = 0
        for user in users:
            with transaction.atomic():
                # قفل کردن رکورد کاربر برای آپدیت دقیق
                user = User.objects.select_for_update().get(pk=user.pk)
                
                left = user.left_volume
                right = user.right_volume
                
                # پیدا کردن پای کمتر (Pay Leg)
                pay_leg_amount = min(left, right)
                
                if pay_leg_amount > 0:
                    # محاسبه سود اولیه
                    commission = pay_leg_amount * BINARY_PERCENT
                    
                    # --- اعمال محدودیت سقف درآمد (Cap) ---
                    # قانون: کل سود دریافتی نباید از X برابر سرمایه فعال بیشتر باشد
                    active_investments = UserInvestment.objects.filter(user=user, status='active')
                    total_invested = sum(inv.amount for inv in active_investments)
                    
                    if total_invested == 0:
                        self.stdout.write(f"User {user.username} skipped (No active investment). Volumes remain.")
                        continue # اگر سرمایه ندارد، سودی نمیگیرد ولی حجمش نمیسوزد (سیاست دلخواه)

                    max_allowed_income = total_invested * 3 # مثلاً ۳ برابر سرمایه
                    
                    # چقدر تا الان سود گرفته؟
                    current_earnings = user.total_commission_earned
                    remaining_cap = max_allowed_income - current_earnings
                    
                    if remaining_cap <= 0:
                         commission = 0
                         self.stdout.write(f"User {user.username} Reached Max Cap. No commission.")
                    elif commission > remaining_cap:
                        commission = remaining_cap # فقط تا سقف پرداخت می‌شود (Flush out مازاد)
                        self.stdout.write(f"User {user.username} Capped. Paid {commission} instead of original amount.")

                    # --- پرداخت و کسر حجم ---
                    if commission > 0:
                        wallet = Wallet.objects.select_for_update().get(user=user)
                        wallet.balance += commission
                        wallet.save()
                        
                        Transaction.objects.create(
                            wallet=wallet,
                            amount=commission,
                            transaction_type='binary_bonus',
                            status='confirmed',
                            description=f"Binary Bonus on {pay_leg_amount} volume"
                        )
                        
                        user.total_commission_earned += commission

                    # کسر حجم تعادل داده شده از هر دو طرف
                    # حجم اضافی در سمت قوی خودبخود باقی می‌ماند چون فقط pay_leg_amount را کم می‌کنیم
                    user.left_volume -= pay_leg_amount
                    user.right_volume -= pay_leg_amount
                    user.save()
                    count += 1

        self.stdout.write(self.style.SUCCESS(f"✅ محاسبه پایان یافت. {count} کاربر سود دریافت کردند."))
