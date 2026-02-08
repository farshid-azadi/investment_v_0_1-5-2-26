import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from apps.investments.models import InvestmentPlan, UserInvestment
from apps.wallet.models import Wallet

User = get_user_model()

class Command(BaseCommand):
    help = 'ایجاد دیتای تست: پلن‌ها، ۳ لیدر، ۳۰۰۰ کاربر باینری نامتقارن (رندوم) و تست خرید'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('شروع عملیات Seed (حالت تصادفی)...'))

        try:
            with transaction.atomic():
                # 1. ساخت پلن‌های سرمایه‌گذاری
                self.create_plans()

                # 2. ساخت ۳ لیدر اصلی
                leaders = self.create_leaders()

                # 3. ساخت کاربران با ساختار درختی نامتقارن و رندوم
                users = self.create_random_binary_users(leaders, total_users=900)

                # 4. انجام خرید برای همه کاربران
                self.simulate_investments(users)

            self.stdout.write(self.style.SUCCESS('عملیات با موفقیت و ساختار درختی نامتقارن پایان یافت!'))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"خطای کلی در اجرا: {e}"))
            import traceback
            traceback.print_exc()

    def create_plans(self):
        plans_data = [
            {'name': 'Standard', 'daily': 1.0, 'min': 10, 'max': 500, 'days': 30},
            {'name': 'Silver', 'daily': 1.5, 'min': 501, 'max': 2000, 'days': 45},
            {'name': 'Gold', 'daily': 2.0, 'min': 2001, 'max': 10000, 'days': 60},
            {'name': 'VIP', 'daily': 2.5, 'min': 10001, 'max': 50000, 'days': 90},
        ]
        created_count = 0
        for p in plans_data:
            plan, created = InvestmentPlan.objects.get_or_create(
                name=p['name'],
                defaults={
                    'daily_interest_rate': Decimal(str(p['daily'])),
                    'min_amount': Decimal(p['min']),
                    'max_amount': Decimal(p['max']),
                    'duration_days': p['days'],
                    'description': f"Sood {p['daily']}% baraye {p['days']} rooz"
                }
            )
            if created:
                created_count += 1
        
        self.stdout.write(f"- {created_count} پلن سرمایه‌گذاری ساخته شد.")

    def create_leaders(self):
        leaders = []
        for i in range(1, 4):
            username = f"Leader_{i}"
            mobile = f"0900000000{i}"

            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'mobile': mobile,
                    'first_name': "Leader",
                    'last_name': str(i)
                }
            )
            if created:
                user.set_password('123456')
                if hasattr(user, 'is_verified'):
                    user.is_verified = True
                user.save()

            # بررسی و ایجاد کیف پول (جهت جلوگیری از خطا اگر سیگنال ساخته باشد)
            Wallet.objects.get_or_create(user=user, defaults={'balance': 0})
            
            leaders.append(user)

        self.stdout.write(f"- ۳ لیدر اصلی آماده شدند.")
        return leaders

    def create_random_binary_users(self, leaders, total_users):
        """
        ایجاد کاربران و جایگذاری آنها به صورت تصادفی در درخت.
        """
        all_existing_users = list(leaders)
        new_users_list = []
        
        # دیکشنری برای نگهداری وضعیت فرزندان در حافظه جهت سرعت بالا
        # format: {user_id: {'left': child_user, 'right': child_user}}
        tree_map = {u.id: {'left': None, 'right': None} for u in leaders}
        
        self.stdout.write(f"- در حال ساخت {total_users} کاربر با ساختار رندوم...")

        for i in range(1, total_users + 1):
            # 1. انتخاب رندوم یک معرف (Sponsor)
            referrer = random.choice(all_existing_users)
            
            mobile_suffix = str(i).zfill(4)
            username = f"User_{i}"
            
            # ساخت آبجکت کاربر (هنوز ذخیره نهایی با parent نشده)
            user = User(
                username=username,
                mobile=f"091200{mobile_suffix}",
                first_name="User",
                last_name=str(i),
                referrer=referrer
            )
            user.set_password('123456')
            if hasattr(user, 'is_verified'):
                user.is_verified = True
            
            # 2. پیدا کردن جایگاه (Placement) با حرکت تصادفی در درخت
            current_node = referrer
            position = None
            parent_found = None

            while True:
                # اضافه کردن نود جاری به نقشه اگر نیست
                if current_node.id not in tree_map:
                    tree_map[current_node.id] = {'left': None, 'right': None}
                
                # بررسی فرزندان
                has_left = tree_map[current_node.id]['left'] is not None
                has_right = tree_map[current_node.id]['right'] is not None

                # تصمیم‌گیری حرکت
                if not has_left and not has_right:
                    position = random.choice(['left', 'right'])
                    parent_found = current_node
                    break 
                
                elif not has_left:
                    # اگر چپ خالیه، با احتمال 70% پر کن، یا برو راست
                    if random.random() < 0.7: 
                        position = 'left'
                        parent_found = current_node
                        break
                    else:
                        current_node = tree_map[current_node.id]['right']
                
                elif not has_right:
                    # اگر راست خالیه، با احتمال 70% پر کن، یا برو چپ
                    if random.random() < 0.7:
                        position = 'right'
                        parent_found = current_node
                        break
                    else:
                        current_node = tree_map[current_node.id]['left']
                
                else:
                    # هر دو پر هستند، رندوم برو پایین
                    direction = random.choice(['left', 'right'])
                    current_node = tree_map[current_node.id][direction]

            # 3. ثبت نهایی کاربر
            user.binary_parent = parent_found
            user.binary_position = position
            user.save()
            
            # 4. ایجاد یا آپدیت کیف پول (اصلاح شده برای جلوگیری از خطای Duplicate)
            random_balance = random.randint(100, 12000)
            
            wallet, created_wallet = Wallet.objects.get_or_create(
                user=user,
                defaults={'balance': Decimal(random_balance)}
            )
            
            # اگر کیف پول از قبل (توسط سیگنال) ساخته شده بود، موجودی‌اش را آپدیت کن
            if not created_wallet:
                wallet.balance = Decimal(random_balance)
                wallet.save()

            # آپدیت مپ حافظه
            if parent_found.id not in tree_map:
                tree_map[parent_found.id] = {'left': None, 'right': None}
            
            tree_map[parent_found.id][position] = user
            tree_map[user.id] = {'left': None, 'right': None} # اضافه کردن خود کاربر جدید

            all_existing_users.append(user)
            new_users_list.append(user)

            if i % 100 == 0:
                self.stdout.write(f"  -- {i} کاربر ساخته شد...")

        return new_users_list

    def simulate_investments(self, users):
        self.stdout.write(self.style.WARNING("- شروع شبیه‌سازی خرید (تست تراکنش امن)..."))
        
        success_count = 0
        fail_count = 0

        for user in users:
            # رفرش کردن موجودی از دیتابیس
            user.wallet.refresh_from_db()
            balance = user.wallet.balance
            
            # پیدا کردن مناسب‌ترین پلن
            plan = InvestmentPlan.objects.filter(
                min_amount__lte=balance,
                max_amount__gte=balance
            ).order_by('-min_amount').first()

            if plan:
                # سرمایه‌گذاری رندوم: یا کل پول یا نصف پول
                invest_portion = random.choice([1.0, 0.5])
                invest_amount = balance * Decimal(invest_portion)
                invest_amount = round(invest_amount, 0)

                if invest_amount < plan.min_amount:
                    invest_amount = plan.min_amount

                try:
                    UserInvestment.objects.create(
                        user=user,
                        plan_type=plan.name,
                        amount=invest_amount,
                        daily_interest_rate=plan.daily_interest_rate,
                        duration_days=plan.duration_days
                    )
                    success_count += 1
                except ValidationError:
                    pass
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"خطا برای {user.username}: {e}"))
                    fail_count += 1
            
        self.stdout.write(f"نتیجه خریدها: {success_count} موفق | {fail_count} ناموفق")
