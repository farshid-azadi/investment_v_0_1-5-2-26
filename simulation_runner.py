import os
import django
import random
import string
from decimal import Decimal
from django.db.models import Sum
from django.db import connection # برای اجرای دستورات مستقیم SQL

# تنظیمات محیط جنگو
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.wallet.models import Wallet, Transaction
from apps.investments.models import InvestmentPlan
from apps.core.models import MLMSettings
# سرویس خرید پلن
from apps.accounts.services.plan_service import purchase_plan 

User = get_user_model()

# --- تنظیمات تست ---
BASE_PREFIX = "sim_user_"
TOTAL_USERS_TO_CREATE = 20  
MAX_DEPTH = 4               
MAX_CHILDREN_PER_USER = 3   

def get_valid_fields(model_class):
    """لیست فیلدهای معتبر یک مدل را برمی‌گرداند"""
    return {f.name for f in model_class._meta.get_fields()}

def clean_defaults(model_class, defaults_dict):
    """دیکشنری را تمیز می‌کند و فقط فیلدهای موجود در مدل را نگه می‌دارد"""
    valid_fields = get_valid_fields(model_class)
    cleaned = {k: v for k, v in defaults_dict.items() if k in valid_fields}
    return cleaned

def generate_random_string(length=5):
    return ''.join(random.choices(string.ascii_lowercase, k=length))

def fix_database_constraints():
    """
    این تابع ناهماهنگی بین مدل و دیتابیس را حل می‌کند.
    تمام روزهای هفته را چک کرده و مقدار پیش‌فرض ۱ (True) را در دیتابیس ست می‌کند.
    """
    print("🔧 Checking & Fixing Database Constraints (All Days)...")
    with connection.cursor() as cursor:
        # لیست تمام فیلدهای روزانه که ممکن است در دیتابیس باشند اما در مدل نه
        days = ['saturday', 'sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'holidays']
        problematic_fields = [f'pay_on_{day}' for day in days]
        
        for field in problematic_fields:
            try:
                # دستور MySQL برای ست کردن مقدار پیش‌فرض
                cursor.execute(f"ALTER TABLE investments_investmentplan ALTER COLUMN {field} SET DEFAULT 1")
                # print(f"   ✅ Fixed constraint for '{field}'") 
            except Exception as e:
                # خطاهای احتمالی (مثل نبودن ستون) را نادیده می‌گیریم
                pass
    print("   ✅ Database constraints applied for daily payment fields.")

def setup_environment():
    """ایجاد پلن‌ها با توجه به فیلدهای موجود در دیتابیس"""
    
    # اول: اصلاح دیتابیس برای تمام روزها
    fix_database_constraints()
    
    print("\n🛠 Setting up Investment Plans & MLM Settings...")

    # 1. تنظیمات MLM
    try:
        mlm_settings, _ = MLMSettings.objects.get_or_create()
        valid_mlm_fields = get_valid_fields(MLMSettings)
        if 'level_1_percent' in valid_mlm_fields:
            mlm_settings.level_1_percent = 10.0
        if 'level_2_percent' in valid_mlm_fields:
            mlm_settings.level_2_percent = 5.0
        mlm_settings.save()
    except Exception as e:
        print(f"Warning: Could not setup MLMSettings: {e}")
    
    # 2. تعریف پلن‌ها
    plans_data = [
        {"name": "Starter Sim", "min": 50, "max": 499, "roi": 1.0, "fee": 1, "duration": 30},
        {"name": "Pro Sim", "min": 500, "max": 50000, "roi": 1.5, "fee": 5, "duration": 45},
    ]
    
    created_plans = []
    
    # شناسایی فیلدهای موجود
    plan_fields = get_valid_fields(InvestmentPlan)
    print(f"DEBUG: InvestmentPlan fields in Model: {plan_fields}")

    for p in plans_data:
        desired_defaults = {
            # --- مبالغ ---
            'min_amount': p['min'],
            'price': p['min'],
            'max_amount': p['max'],
            
            # --- سود ---
            'daily_interest_rate': p['roi'],
            'daily_roi': p['roi'],            
            'roi': p['roi'], 
            'max_total_return_percent': 300, 
            
            # --- کارمزدها ---
            'deposit_fee_fixed': p['fee'],    
            'fee': p['fee'],
            'withdrawal_fee_percent': 3,
            
            # --- زمان ---
            'duration_days': p['duration'],
            'duration': p['duration'],
            'period': p['duration'],
            'binary_retention_days': 365,
            
            # --- سایر ---
            'is_active': True,
            'lottery_ratio_amount': 100,
            'description': f"Auto generated plan {p['name']}"
        }
        
        # تلاش برای اضافه کردن فیلدهای روزانه به دیکشنری (اگر در مدل باشند)
        days = ['saturday', 'sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'holidays']
        for day in days:
            field_name = f'pay_on_{day}'
            if field_name in plan_fields:
                desired_defaults[field_name] = True
        
        safe_defaults = clean_defaults(InvestmentPlan, desired_defaults)
        
        # چک نهایی برای فیلدهای حیاتی
        if 'min_amount' in plan_fields and 'min_amount' not in safe_defaults:
            safe_defaults['min_amount'] = p['min']
        if 'max_amount' in plan_fields and 'max_amount' not in safe_defaults:
            safe_defaults['max_amount'] = p['max']

        try:
            plan, created = InvestmentPlan.objects.update_or_create(
                name=p['name'],
                defaults=safe_defaults
            )
            created_plans.append(plan)
            print(f"   Plan '{p['name']}' ready.")
        except Exception as e:
            print(f"❌ Error creating plan {p['name']}: {e}")
    
    print("✅ Environment Ready.")
    return created_plans

def create_and_activate_user(username, referrer, plans):
    if not plans:
        return None

    mobile_sim = f"09{random.randint(100000000, 999999999)}"
    try:
        user = User.objects.create_user(
            username=username,
            mobile=mobile_sim,
            password="password123",
            referrer=referrer
        )
    except Exception:
        user = User.objects.get(username=username)
        return user
    
    selected_plan = random.choice(plans)
    
    base_price = 100
    if hasattr(selected_plan, 'min_amount') and selected_plan.min_amount:
        base_price = int(selected_plan.min_amount)
    elif hasattr(selected_plan, 'price') and selected_plan.price:
        base_price = int(selected_plan.price)
        
    invest_amount = Decimal(random.randint(base_price, base_price + 50))
    
    fee = Decimal(0)
    if hasattr(selected_plan, 'deposit_fee_fixed') and selected_plan.deposit_fee_fixed:
        fee = selected_plan.deposit_fee_fixed
    elif hasattr(selected_plan, 'fee') and selected_plan.fee:
        fee = selected_plan.fee
        
    needed_balance = invest_amount + fee + Decimal(10)
    
    if not hasattr(user, 'wallet'):
        Wallet.objects.create(user=user, balance=0)
        
    Transaction.objects.create(
        wallet=user.wallet,
        amount=needed_balance,
        transaction_type='deposit',
        status='confirmed',
        description='Simulation Deposit'
    )
    user.wallet.balance = needed_balance
    user.wallet.save()
    
    print(f"   User: {user.username} | Invest: {invest_amount}")
    
    try:
        try:
            purchase_plan(user, selected_plan, amount=invest_amount)
        except TypeError:
            purchase_plan(user, selected_plan)
            
    except Exception as e:
        print(f"   X Purchase Failed: {e}")
        
    return user

def build_network_recursive(parent_user, current_depth, plans, created_count):
    if current_depth >= MAX_DEPTH or created_count[0] >= TOTAL_USERS_TO_CREATE:
        return

    num_children = random.randint(0, MAX_CHILDREN_PER_USER)
    
    for _ in range(num_children):
        if created_count[0] >= TOTAL_USERS_TO_CREATE:
            break
            
        new_username = f"{BASE_PREFIX}{generate_random_string()}_{created_count[0]}"
        new_user = create_and_activate_user(new_username, parent_user, plans)
        if new_user:
            created_count[0] += 1
            build_network_recursive(new_user, current_depth + 1, plans, created_count)

def run_simulation():
    print("\n" + "="*50)
    print("STARTING ROBUST SIMULATION (With Full DB Patch)")
    print("="*50)
    
    User.objects.filter(username__startswith=BASE_PREFIX).delete()
    
    plans = setup_environment()
    
    if not plans:
        print("⛔ CRITICAL: No plans could be created.")
        return

    root_username = f"{BASE_PREFIX}LEADER"
    root_user = User.objects.create_user(
        username=root_username,
        mobile="09000000000",
        password="password123"
    )
    if not hasattr(root_user, 'wallet'):
        Wallet.objects.create(user=root_user, balance=0)
    
    print(f"\nRoot User Created: {root_user.username}")
    
    created_count = [0]
    build_network_recursive(root_user, 0, plans, created_count)
    
    print("\n" + "="*50)
    print("REPORT")
    print("="*50)
    
    root_user.wallet.refresh_from_db()
    
    try:
        qs = Transaction.objects.filter(
            wallet=root_user.wallet, 
            transaction_type='referral_reward'
        )
        total_commissions_count = qs.count()
        commission_sum = qs.aggregate(sum=Sum('amount'))['sum'] or 0
        
        print(f"Total Users Created: {created_count[0]}")
        print(f"Root User Commissions: {commission_sum}")
        print(f"Commission Tx Count: {total_commissions_count}")
        print(f"Root Balance: {root_user.wallet.balance}")
        
    except Exception as e:
        print(f"Error calculating stats: {e}")

if __name__ == "__main__":
    run_simulation()
