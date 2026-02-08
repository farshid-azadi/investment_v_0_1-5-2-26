# apps/investments/management/commands/pay_daily_profits.py

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from apps.investments.models import UserInvestment
from apps.wallet.models import Transaction, Wallet
from django.conf import settings # برای خواندن درصدهای سود از سود
from decimal import Decimal

class Command(BaseCommand):
    help = 'توزیع سود روزانه + سود معرف‌ها (Matching Bonus)'

    def handle(self, *args, **options):
        self.stdout.write("--- شروع توزیع سود روزانه و پاداش لیدرها ---")

        # تعریف درصدهای سود از سود برای سطوح (سطح ۱، سطح ۲، سطح ۳)
        # یعنی لیدر سطح ۱: ۵٪ از سود کاربر را میگیرد
        # لیدر سطح ۲: ۲٪ از سود کاربر را میگیرد
        MATCHING_BONUS_LEVELS = [5, 2, 1] 

        active_investments = UserInvestment.objects.filter(status='active')
        count = 0
        total_payout = Decimal('0.00')

        for inv in active_investments:
            days_passed = (timezone.now() - inv.created_at).days

            if days_passed >= inv.plan.duration_days:
                inv.status = 'completed'
                inv.save()
                continue

            # 1. محاسبه سود خود کاربر
            daily_profit = (inv.amount * inv.plan.daily_roi) / 100

            try:
                with transaction.atomic():
                    # الف) واریز سود به کاربر
                    Transaction.objects.create(
                        wallet=inv.user.wallet,
                        amount=daily_profit,
                        transaction_type='profit',
                        status='confirmed',
                        description=f'سود روزانه پلن: {inv.plan.name}'
                    )
                    inv.total_earnings += daily_profit
                    inv.save()
                    
                    # ب) واریز سود به معرف‌ها (Matching Bonus)
                    current_referrer = inv.user.referrer
                    
                    for level_percent in MATCHING_BONUS_LEVELS:
                        if not current_referrer:
                            break

                        # محاسبه سهم لیدر از سود روزانه کاربر
                        leader_profit = (daily_profit * Decimal(level_percent)) / 100

                        if leader_profit > 0:
                            # واریز به کیف پول لیدر
                            Transaction.objects.create(
                                wallet=current_referrer.wallet,
                                amount=leader_profit,
                                transaction_type='referral_reward', # یا نوع جدیدی مثل matching_bonus
                                status='confirmed',
                                description=f'سود از سود روزانه کاربر {inv.user.username}'
                            )
                        
                        # رفتن به لیدر بعدی
                        current_referrer = current_referrer.referrer

                    count += 1
                    total_payout += daily_profit

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error inv {inv.id}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"تعداد پردازش: {count} | کل سود توزیع شده: {total_payout}"))
