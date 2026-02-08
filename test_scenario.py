import os
import django
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from django.core.management import call_command
from django.db import transaction as db_transaction

# تنظیم محیط جنگو
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.accounts.models import User
from apps.wallet.models import Wallet, Transaction
from apps.investments.models import InvestmentPlan, UserInvestment

def run_test():
    print("="*50)
    print("🚀 STARTING COMPREHENSIVE FINANCIAL SYSTEM TEST")
    print("="*50)

    # 1. پاکسازی دیتای تست قبلی (اگر یوزری با این نام باشد)
    User.objects.filter(username='tester_pro').delete()
    
    # 2. ساخت پلن‌های تست
    print("\n[1] Creating Investment Plans...")
    plan_silver, _ = InvestmentPlan.objects.get_or_create(
        name="Silver Test",
        defaults={
            'min_amount': 10, 'max_amount': 1000,
            'daily_roi': 1.0, 'duration_days': 5, # 1% سود برای 5 روز
            'description': 'Test Plan'
        }
    )
    print(f"✅ Plan Created: {plan_silver.name} (ROI: {plan_silver.daily_roi}%, Duration: {plan_silver.duration_days} days)")

    # 3. ساخت کاربر و کیف پول
    print("\n[2] Creating User & Wallet...")
    user = User.objects.create_user(username='tester_pro', mobile='09120000000', password='password123')
    wallet = user.wallet
    print(f"✅ User Created: {user.username}")
    print(f"✅ Wallet Created. Initial Balance: {wallet.balance}")

    # 4. تست واریز (Deposit)
    print("\n[3] Testing Deposit (1000 USDT)...")
    Transaction.objects.create(
        wallet=wallet,
        amount=1000,
        transaction_type='deposit',
        status='confirmed'
    )
    wallet.refresh_from_db()
    if wallet.balance == 1000:
        print(f"✅ Deposit Success. Balance: {wallet.balance}")
    else:
        print(f"❌ Deposit Failed! Balance: {wallet.balance}")
        return

    # 5. تست سرمایه‌گذاری (Investment)
    print("\n[4] Testing Investment Purchase (100 USDT)...")
    # خرید پلن 100 دلاری
    inv = UserInvestment.objects.create(
        user=user,
        plan=plan_silver,
        amount=100
    )
    wallet.refresh_from_db()
    
    # موجودی باید 900 شده باشد (1000 - 100)
    if wallet.balance == 900:
        print(f"✅ Balance Deducted correctly. Current Balance: {wallet.balance}")
    else:
        print(f"❌ Balance Error! Expected 900, got {wallet.balance}")

    # چک کردن تراکنش کسر پول
    inv_txn = Transaction.objects.filter(wallet=wallet, transaction_type='investment').last()
    if inv_txn and inv_txn.amount == 100:
        print("✅ Investment Transaction record found.")
    else:
        print("❌ Investment Transaction record MISSING.")

    # 6. تست سود روزانه (Daily Profit)
    print("\n[5] Testing Daily Profit Distribution...")
    # سود 1% از 100 دلار میشود 1 دلار.
    
    call_command('pay_daily_profits')
    
    wallet.refresh_from_db()
    inv.refresh_from_db()
    
    # موجودی باید 900 + 1 = 901 باشد
    if wallet.balance == 901:
        print(f"✅ Profit Received. Balance: {wallet.balance}")
    else:
        print(f"❌ Profit Error! Expected 901, got {wallet.balance}")

    if inv.total_earnings == 1:
        print(f"✅ Investment Total Earnings updated: {inv.total_earnings}")
    else:
        print(f"❌ Investment Earnings Error! Got {inv.total_earnings}")

    # 7. تست پایان دوره (Expiry Simulation)
    print("\n[6] Testing Plan Expiration...")
    # دستکاری زمان: فرض کنیم 6 روز گذشته است (پلن 5 روزه است)
    inv.created_at = timezone.now() - timedelta(days=6)
    inv.save()
    
    print("   -> Time travelled 6 days into the future...")
    
    # اجرای مجدد سوددهی
    call_command('pay_daily_profits')
    
    inv.refresh_from_db()
    wallet.refresh_from_db()
    
    if inv.status == 'completed':
        print(f"✅ Plan correctly marked as 'completed'.")
    else:
        print(f"❌ Plan status Error! Status is: {inv.status}")
        
    # موجودی نباید تغییر کرده باشد (چون تمام شده)
    if wallet.balance == 901: # همان مقدار مرحله قبل
        print(f"✅ No extra profit paid after expiry. Balance stable at {wallet.balance}")
    else:
        print(f"❌ Error! User received profit after expiry! Balance: {wallet.balance}")

    # 8. تست عدم موجودی (Insufficient Funds)
    print("\n[7] Testing Insufficient Funds...")
    try:
        # موجودی فعلی 901 است. تلاش برای خرید 5000 تتر
        UserInvestment.objects.create(
            user=user,
            plan=plan_silver,
            amount=5000
        )
        print("❌ FAILED: System allowed purchase with insufficient funds!")
    except ValueError as e:
        print(f"✅ BLOCKED: Correctly raised error: {e}")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")

    print("\n" + "="*50)
    print("🏁 TEST COMPLETED")
    print("="*50)

if __name__ == "__main__":
    run_test()
