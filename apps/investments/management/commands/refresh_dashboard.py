from django.core.management.base import BaseCommand
from django.db.models import Sum
from apps.accounts.models import User
from apps.investments.models import UserInvestment

# تلاش برای ایمپورت سرویس محاسبه حجم. اگر نباشد، از آن رد می‌شویم
try:
    from apps.network.services import update_binary_volumes
    HAS_BINARY_SERVICE = True
except ImportError:
    HAS_BINARY_SERVICE = False

class Command(BaseCommand):
    help = 'Update Dashboard Stats (Volume & Profit) without destroying the tree'

    def handle(self, *args, **options):
        self.stdout.write("--- شروع به‌روزرسانی داشبورد (نسخه اصلاح شده) ---")

        # 1. صفر کردن حجم‌های فعلی برای محاسبه دقیق
        self.stdout.write("صفر کردن حجم‌ها برای محاسبه مجدد...")
        User.objects.all().update(left_volume=0, right_volume=0)

        # 2. محاسبه مجدد حجم‌های باینری (L/R)
        if HAS_BINARY_SERVICE:
            investments = UserInvestment.objects.filter(status='active')
            self.stdout.write(f"محاسبه حجم باینری برای {investments.count()} سرمایه‌گذاری فعال...")
            
            for invest in investments:
                try:
                    if invest.user.binary_parent:
                         update_binary_volumes(invest.user, invest.amount)
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error updating volume for {invest.user}: {e}"))
        else:
            self.stdout.write(self.style.WARNING("سرویس update_binary_volumes یافت نشد. محاسبه حجم نادیده گرفته شد."))

        # 3. همگام‌سازی سود کل (Total Profit) با دیتابیس
        self.stdout.write("همگام‌سازی سود نمایش داده شده با داده‌های واقعی...")
        users = User.objects.all()
        for user in users:
            # --- اصلاح شده: استفاده از نام فیلد صحیح total_profit_earned ---
            real_total_profit = UserInvestment.objects.filter(user=user).aggregate(Sum('total_profit_earned'))['total_profit_earned__sum'] or 0
            
            updated = False
            
            # پیدا کردن فیلد مناسب در مدل User برای ذخیره
            if hasattr(user, 'total_profit_earned'): 
                user.total_profit_earned = real_total_profit
                updated = True
            elif hasattr(user, 'total_profit'):
                user.total_profit = real_total_profit
                updated = True
            elif hasattr(user, 'total_earned'):
                user.total_earned = real_total_profit
                updated = True
            
            if updated:
                user.save()

        self.stdout.write(self.style.SUCCESS("✅ داشبورد با موفقیت آپدیت شد. صفحه را رفرش کنید."))

        self.stdout.write("--- به‌روزرسانی داشبورد (نسخه اصلاح شده) ---")