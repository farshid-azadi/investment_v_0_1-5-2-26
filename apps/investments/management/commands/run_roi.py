from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.investments.models import UserPlan  # نام مدل پلن خود را چک کنید
from apps.accounts.services.roi_service import calculate_roi # فرض بر وجود این سرویس

class Command(BaseCommand):
    help = 'Process Daily ROI for active investments'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting ROI calculation...")
        
        # پیدا کردن تمام سرمایه‌گذاری‌های فعال
        active_plans = UserPlan.objects.filter(status='active')
        
        count = 0
        for plan in active_plans:
            # اینجا تابع محاسبه سود را صدا می‌زنیم
            # اگر این تابع را ندارید، منطق ساده زیر را تست کنید:
            
            daily_profit = plan.active_capital * (plan.plan.daily_percent / 100)
            
            # اضافه کردن به سود کل پلن
            plan.total_profit_earned += daily_profit
            plan.save()
            
            # اضافه کردن به کیف پول کاربر
            wallet = plan.user.wallet
            wallet.balance += daily_profit
            wallet.save()
            
            count += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully processed ROI for {count} plans.'))

#### قدم دوم: اجرای دستی محاسبه سود


 

#### قدم سوم: آپدیت دستی حجم‌های باینری (برای اعداد درخت)






from django.core.management.base import BaseCommand
from apps.accounts.models import User
from apps.investments.models import UserPlan
from django.db.models import Sum

class Command(BaseCommand):
    help = 'Recalculate Binary Volumes'

    def handle(self, *args, **kwargs):
        users = User.objects.all()
        for user in users:
            # محاسبه حجم فروش سمت چپ
            left_volume = 0
            left_child = user.binary_children.filter(binary_position='left').first()
            if left_child:
                # این یک محاسبه ساده است، در واقعیت باید بازگشتی (Recursive) کل زیرمجموعه چپ را جمع بزنید
                # اینجا فرض میکنیم فقط حجم خودِ فرزند مستقیم را میخواهیم برای تست
                plans = UserPlan.objects.filter(user=left_child, status='active')
                left_volume = plans.aggregate(Sum('active_capital'))['active_capital__sum'] or 0

            # محاسبه حجم فروش سمت راست
            right_volume = 0
            right_child = user.binary_children.filter(binary_position='right').first()
            if right_child:
                plans = UserPlan.objects.filter(user=right_child, status='active')
                right_volume = plans.aggregate(Sum('active_capital'))['active_capital__sum'] or 0
            
            # ذخیره در دیتابیس (فیلدهای کش شده روی مدل User)
            # فرض بر این است که مدل User فیلدهای left_volume و right_volume دارد
            # user.left_sales = left_volume
            # user.right_sales = right_volume
            # user.save()
            
            self.stdout.write(f"User {user.username}: L={left_volume} | R={right_volume}")

