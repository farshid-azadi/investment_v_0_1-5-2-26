# apps/investments/management/commands/fix_binary_tree.py

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F
from apps.accounts.models import User
from apps.investments.models import UserInvestment
from apps.network.services import update_binary_volumes

class Command(BaseCommand):
    help = 'چیدمان مجدد کاربران موجود در ساختار باینری و محاسبه مجدد حجم‌ها'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("--- شروع اصلاح ساختار باینری ---"))

        # 1. پاکسازی دیتای باینری فعلی (ریست کردن)
        User.objects.all().update(
            binary_parent=None,
            binary_position=None,
            left_volume=0,
            right_volume=0
        )
        self.stdout.write("دیتای باینری قبلی ریست شد.")

        # 2. پیدا کردن لیدرها
        leaders = list(User.objects.filter(username__startswith='Leader').order_by('id'))
        if not leaders:
            self.stdout.write(self.style.ERROR("لیدری یافت نشد! ابتدا seed_mlm_test را اجرا کنید."))
            return

        # 3. پیدا کردن کاربران عادی
        users_pool = list(User.objects.filter(username__startswith='User_').order_by('id'))
        
        self.stdout.write(f"{len(leaders)} لیدر و {len(users_pool)} کاربر پیدا شد.")

        # 4. توزیع کاربران بین لیدرها (برای اینکه هر لیدر زیرمجموعه داشته باشد)
        # به هر لیدر یک لیست از کاربران اختصاص می‌دهیم
        users_per_leader = len(users_pool) // len(leaders)
        
        start_index = 0
        with transaction.atomic():
            for i, leader in enumerate(leaders):
                end_index = start_index + users_per_leader
                # اگر لیدر آخر است، همه باقی‌مانده‌ها را بگیرد
                if i == len(leaders) - 1:
                    my_users = users_pool[start_index:]
                else:
                    my_users = users_pool[start_index:end_index]
                
                start_index = end_index
                
                self.stdout.write(f"چیدمان {len(my_users)} کاربر زیر مجموعه {leader.username}...")
                self.build_tree_for_leader(leader, my_users)

            # 5. محاسبه مجدد حجم‌ها (Volumes) بر اساس خریدهای انجام شده
            self.recalculate_volumes()

        self.stdout.write(self.style.SUCCESS("\n--- عملیات با موفقیت پایان یافت! ادمین را چک کنید ---"))

    def build_tree_for_leader(self, root_user, users_list):
        """
        این تابع کاربران را به روش BFS (لایه به لایه) زیر نظر ریشه می‌چیند.
        """
        queue = [root_user] # صفی از پدرانی که دنبال فرزند هستند
        
        current_user_idx = 0
        total_users = len(users_list)

        while current_user_idx < total_users:
            if not queue:
                break
            
            parent = queue[0] # پدر فعلی را از ابتدای صف بردار
            
            # تلاش برای پر کردن سمت چپ
            if current_user_idx < total_users:
                child = users_list[current_user_idx]
                child.binary_parent = parent
                child.binary_position = 'left'
                child.save()
                
                queue.append(child) # این فرزند خودش میشه پدر آینده
                current_user_idx += 1
            
            # تلاش برای پر کردن سمت راست
            if current_user_idx < total_users:
                child = users_list[current_user_idx]
                child.binary_parent = parent
                child.binary_position = 'right'
                child.save()
                
                queue.append(child)
                current_user_idx += 1
            
            # پدر فعلی پر شد، از صف خارجش کن تا بریم سراغ نفر بعدی در صف
            queue.pop(0)

    def recalculate_volumes(self):
        """
        چون ساختار را تغییر دادیم، باید حجم فروش‌ها را دوباره محاسبه کنیم.
        """
        self.stdout.write("در حال محاسبه مجدد حجم فروش‌ها...")
        
        # تمام سرمایه‌گذاری‌های فعال را پیدا کن
        investments = UserInvestment.objects.filter(status='active').select_related('user')
        
        count = 0
        for invest in investments:
            # تابع سرویس ما حجم را به سمت بالا در درخت جدید پخش می‌کند
            update_binary_volumes(invest.user, invest.amount)
            count += 1
            
        self.stdout.write(f"حجم فروش برای {count} سرمایه‌گذاری محاسبه شد.")
