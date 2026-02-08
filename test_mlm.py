import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.accounts.models import User
from apps.wallet.models import Transaction
from apps.investments.models import InvestmentPlan, UserInvestment

def run_mlm_test():
    print("="*50)
    print("🚀 STARTING MLM / REFERRAL SYSTEM TEST")
    print("="*50)

    # 1. پاکسازی دیتای قبلی
    User.objects.filter(username__in=['user_A', 'user_B', 'user_C']).delete()
    
    # 2. ساخت پلن تست
    plan, _ = InvestmentPlan.objects.get_or_create(
        name="MLM Starter",
        defaults={'daily_roi': 1.0, 'duration_days': 10, 'min_amount': 10}
    )

    # 3. ساخت ساختار درختی کاربران
    # ساختار: User A -> دعوت میکند -> User B -> دعوت میکند -> User C
    
    print("[1] Creating User Chain (A -> B -> C)...")
    
    # User A (Leader)
    user_a = User.objects.create_user(username='user_A', mobile='09100000001', password='password123')
    
    # User B (Level 1 of A)
    user_b = User.objects.create_user(username='user_B', mobile='09100000002', password='password123', referrer=user_a)
    
    # User C (Level 2 of A, Level 1 of B)
    user_c = User.objects.create_user(username='user_C', mobile='09100000003', password='password123', referrer=user_b)

    print("✅ Users Created and Linked.")

    # 4. شارژ کیف پول نفر آخر (User C) برای خرید
    print("\n[2] Charging User C Wallet...")
    user_c.wallet.balance = 1000
    user_c.wallet.save()
    print(f"✅ User C Balance: {user_c.wallet.balance}")

    # 5. انجام سرمایه‌گذاری توسط User C
    print("\n[3] User C invests 100 USDT...")
    UserInvestment.objects.create(user=user_c, plan=plan, amount=100)
    
    # موجودی C باید 900 شود
    user_c.wallet.refresh_from_db()
    print(f"✅ User C new balance: {user_c.wallet.balance} (Expected 900)")

    # 6. بررسی پورسانت‌ها
    print("\n[4] Checking Commissions...")
    
    # User B (معرف مستقیم - سطح 1)
    # طبق تنظیمات: 10% از 100 دلار = 10 دلار
    user_b.wallet.refresh_from_db()
    txn_b = Transaction.objects.filter(wallet=user_b.wallet, transaction_type='referral_reward').first()
    
    print(f"   -> User B Balance: {user_b.wallet.balance}")
    if user_b.wallet.balance == 10 and txn_b:
        print("✅ User B received Level 1 commission (10 USDT).")
    else:
        print(f"❌ User B Failed! Balance: {user_b.wallet.balance}")

    # User A (معرفِ معرف - سطح 2)
    # طبق تنظیمات: 5% از 100 دلار = 5 دلار
    user_a.wallet.refresh_from_db()
    txn_a = Transaction.objects.filter(wallet=user_a.wallet, transaction_type='referral_reward').first()
    
    print(f"   -> User A Balance: {user_a.wallet.balance}")
    if user_a.wallet.balance == 5 and txn_a:
        print("✅ User A received Level 2 commission (5 USDT).")
    else:
        print(f"❌ User A Failed! Balance: {user_a.wallet.balance}")

    print("\n" + "="*50)
    print("🏁 MLM TEST COMPLETED")
    print("="*50)

if __name__ == "__main__":
    run_mlm_test()
