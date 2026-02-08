import os
import django
import random
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone

# تنظیم محیط جنگو
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.accounts.models import User, BinaryTree
from apps.wallet.models import Wallet, Transaction
from apps.investments.models import InvestmentPlan, UserInvestment
from apps.accounts.services.plan_service import purchase_plan

User = get_user_model()

def create_realistic_test_network():
    print("="*60)
    print("🌐 ساخت شبکه تست 200 نفره با خرید پلن‌های تصادفی")
    print("="*60)
    
    # 1. پاکسازی داده‌های تست قبلی
    print("🧹 پاکسازی کاربران تست قبلی...")
    User.objects.filter(username__startswith="test_user_").delete()
    
    # 2. ساخت پلن‌های سرمایه‌گذاری
    print("\n📋 ایجاد پلن‌های سرمایه‌گذاری...")
    plans = [
        {"name": "Starter", "min": 25, "roi": 0.5, "fee": 2},
        {"name": "Basic", "min": 50, "roi": 0.75, "fee": 2},
        {"name": "Standard", "min": 100, "roi": 1.0, "fee": 2},
        {"name": "Silver", "min": 500, "roi": 1.25, "fee": 3},
        {"name": "Gold", "min": 1000, "roi": 1.5, "fee": 3},
    ]
    
    for p in plans:
        InvestmentPlan.objects.update_or_create(
            name=p['name'],
            defaults={
                'min_amount': p['min'],
                'daily_roi': p['roi'],
                'deposit_fee_fixed': p['fee'],
                'duration_days': 30,
                'is_active': True
            }
        )
    
    # 3. ساخت کاربر ریشه (ادمین)
    print("\n👑 ایجاد کاربر ریشه...")
    root_user = User.objects.create_superuser(
        username="admin_root",
        mobile="09000000000",
        password="admin123"
    )
    Wallet.objects.create(user=root_user, balance=10000)
    
    # 4. ساخت 200 کاربر تستی
    print("\n👥 ایجاد 200 کاربر تستی...")
    users = []
    for i in range(1, 201):
        user = User.objects.create_user(
            username=f"test_user_{i}",
            mobile=f"0912{i:06d}",
            password="test123"
        )
        Wallet.objects.create(user=user)
        users.append(user)
        print(f"✅ کاربر {i}/200 ایجاد شد", end="\r")
    
    # 5. ساخت ساختار شبکه تصادفی
    print("\n\n🌳 ساخت ساختار شبکه تصادفی...")
    for i, user in enumerate(users):
        if i == 0:
            # اولین کاربر زیرمجموعه ریشه
            BinaryTree.objects.create(
                user=user,
                parent=root_user,
                position='left' if random.random() < 0.5 else 'right'
            )
        else:
            # انتخاب تصادفی یک کاربر قبلی به عنوان والد
            parent = random.choice(users[:i])
            BinaryTree.objects.create(
                user=user,
                parent=parent,
                position='left' if random.random() < 0.5 else 'right'
            )
        print(f"✅ ساختار شبکه برای کاربر {i+1}/200 تکمیل شد", end="\r")
    
    # 6. شارژ کیف پول و خرید پلن‌ها
    print("\n\n💰 شارژ کیف پول و خرید پلن‌ها...")
    all_plans = list(InvestmentPlan.objects.all())
    investment_count = 0
    
    for user in users:
        # شارژ کیف پول (بین 50 تا 1500 دلار)
        deposit_amount = Decimal(str(random.randint(50, 1500)))
        Transaction.objects.create(
            wallet=user.wallet,
            amount=deposit_amount,
            transaction_type='deposit',
            status='confirmed'
        )
        user.wallet.balance += deposit_amount
        user.wallet.save()
        
        # انتخاب تصادفی یک پلن
        plan = random.choice(all_plans)
        amount = Decimal(str(random.randint(
            int(plan.min_amount),
            int(plan.min_amount * 3)
        )))
        
        # خرید پلن اگر موجودی کافی باشد
        try:
            purchase_plan(user=user, plan=plan, amount=amount)
            investment_count += 1
            print(f"✅ خرید پلن {plan.name} به مبلغ {amount} برای کاربر {user.username}", end="\r")
        except Exception as e:
            print(f"⚠️ خطا در خرید پلن برای کاربر {user.username}: {str(e)}")
    
    # 7. گزارش نهایی
    print("\n\n📊 گزارش نهایی:")
    print("="*60)
    print(f"تعداد کاربران: {User.objects.count()}")
    print(f"تعداد خریدهای انجام شده: {investment_count}")
    print(f"تعداد پلن‌های فعال: {UserInvestment.objects.count()}")
    
    total_invested = sum(
        inv.amount for inv in UserInvestment.objects.all()
    )
    print(f"حجم کل سرمایه‌گذاری: ${total_invested}")
    
    # محاسبه حجم‌های باینری
    root_left = sum(
        user.left_volume for user in User.objects.all()
    )
    root_right = sum(
        user.right_volume for user in User.objects.all()
    )
    print(f"حجم کل چپ شبکه: ${root_left}")
    print(f"حجم کل راست شبکه: ${root_right}")
    print("="*60)
    print("✅ تست با موفقیت انجام شد!")

if __name__ == "__main__":
    create_realistic_test_network()
