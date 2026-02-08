# apps/investments/management/commands/run_daily_profit.py

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from apps.investments.models import UserInvestment, ReferralLevel
from apps.wallet.models import Transaction, Wallet

class Command(BaseCommand):
    help = 'توزیع سود روزانه + سود معرف‌ها (بر اساس تنظیمات پنل ادمین)'

    def handle(self, *args, **options):
        self.stdout.write("⏳ شروع محاسبات سود روزانه و پاداش شبکه...")

        # 1. دریافت تنظیمات سطوح از دیتابیس و ساخت یک دیکشنری برای دسترسی سریع
        # مثال ساختار: {1: 5.0, 2: 2.0, 3: 0.025}
        levels_config = {
            lvl.level: lvl.daily_profit_commission 
            for lvl in ReferralLevel.objects.all()
        }
        max_level = max(levels_config.keys()) if levels_config else 0
        
        self.stdout.write(f"ℹ️ تنظیمات شبکه: {len(levels_config)} سطح فعال یافت شد.")

        active_investments = UserInvestment.objects.filter(status='active')
        count = 0
        total_payout = Decimal('0.00')

        for inv in active_investments:
            # بررسی پایان دوره پلن
            if inv.total_profit_earned >= (inv.amount * 3): # مثال: سقف 300 درصد
                 # یا شرط زمانی
                 days_passed = (timezone.now() - inv.created_at).days
                 if days_passed >= inv.duration_days:
                     inv.status = 'completed'
                     inv.save()
                     continue

            # محاسبه سود روزانه خود کاربر
            # فرمول: مبلغ سرمایه * درصد روزانه / 100
            daily_profit = (inv.amount * inv.daily_interest_rate) / 100
            
            # گرد کردن تا 4 رقم اعشار برای دقت
            daily_profit = daily_profit.quantize(Decimal("0.0001"))

            try:
                with transaction.atomic():
                    # --- بخش الف: واریز به خود کاربر ---
                    wallet = inv.user.wallet
                    # استفاده از select_for_update برای جلوگیری از Race Condition
                    wallet = Wallet.objects.select_for_update().get(pk=wallet.pk)
                    
                    wallet.balance += daily_profit
                    wallet.save()

                    Transaction.objects.create(
                        wallet=wallet,
                        amount=daily_profit,
                        transaction_type='daily_profit', # نوع باید در مدل باشد یا به invest/profit مپ شود
                        status='confirmed',
                        description=f'Daily Profit - Plan: {inv.plan_type}'
                    )

                    inv.total_profit_earned += daily_profit
                    inv.save()
                    
                    # --- بخش ب: واریز به معرف‌ها (دینامیک از دیتابیس) ---
                    current_referrer = inv.user.referrer
                    current_level = 1

                    while current_referrer and current_level <= max_level:
                        # دریافت درصد سود برای این سطح از تنظیمات دیتابیس
                        level_percent = levels_config.get(current_level, Decimal('0'))

                        if level_percent > 0:
                            # محاسبه پاداش: درصدی از "سود روزانه کاربر"
                            leader_reward = (daily_profit * level_percent) / 100
                            leader_reward = leader_reward.quantize(Decimal("0.0001"))

                            if leader_reward > 0:
                                leader_wallet = Wallet.objects.select_for_update().get(pk=current_referrer.wallet.pk)
                                leader_wallet.balance += leader_reward
                                leader_wallet.save()

                                Transaction.objects.create(
                                    wallet=leader_wallet,
                                    amount=leader_reward,
                                    transaction_type='referral_reward',
                                    status='confirmed',
                                    description=f'Matching Bonus L{current_level} from user {inv.user.username}'
                                )
                        
                        # حرکت به لیدر سطح بالاتر
                        current_referrer = current_referrer.referrer
                        current_level += 1

                    count += 1
                    total_payout += daily_profit

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Error for Investment ID {inv.id}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"✅ پایان عملیات. {count} پردازش انجام شد. کل سود توزیع شده: {total_payout}"))
