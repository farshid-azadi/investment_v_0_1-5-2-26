# apps/accounts/management/commands/rebuild_tree.py
from django.core.management.base import BaseCommand
from apps.accounts.models import User
import random

class Command(BaseCommand):
    help = 'Rebuilds binary tree structure randomly for existing users'

    def handle(self, *args, **kwargs):
        # 1. پاک کردن اتصالات قبلی
        User.objects.update(binary_parent=None, binary_position=None)
        self.stdout.write("اتصالات قبلی پاک شد.")

        # 2. پیدا کردن یا ساختن لیدرها
        leaders = ["Leader_1", "Leader_2", "Leader_3"]
        root_nodes = []
        
        for name in leaders:
            u, _ = User.objects.get_or_create(username=name, defaults={'mobile': f'0912000000{random.randint(1,9)}'})
            root_nodes.append(u)
        
        # 3. اتصال بقیه کاربران به لیدرها
        all_users = list(User.objects.exclude(username__in=leaders).exclude(is_superuser=True))
        
        # صف برای پر کردن لایه به لایه (BFS)
        # ساختار صف: (ParentUser, Side)
        # ما سه درخت جداگانه می‌سازیم
        
        current_index = 0
        
        for root in root_nodes:
            self.stdout.write(f"--- ساخت درخت برای {root.username} ---")
            queue = [root]
            
            while queue and current_index < len(all_users):
                parent = queue.pop(0)
                
                # تلاش برای پر کردن سمت چپ
                if current_index < len(all_users):
                    child = all_users[current_index]
                    child.binary_parent = parent
                    child.binary_position = 'left'
                    child.save()
                    queue.append(child)
                    current_index += 1
                    # self.stdout.write(f"  {child.username} -> Left of {parent.username}")

                # تلاش برای پر کردن سمت راست
                if current_index < len(all_users):
                    child = all_users[current_index]
                    child.binary_parent = parent
                    child.binary_position = 'right'
                    child.save()
                    queue.append(child)
                    current_index += 1
                    # self.stdout.write(f"  {child.username} -> Right of {parent.username}")

        self.stdout.write(self.style.SUCCESS(f"درخت باینری با موفقیت بازسازی شد!"))
