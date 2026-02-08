# apps/investments/management/commands/show_tree.py

from django.core.management.base import BaseCommand
from apps.accounts.models import User

class Command(BaseCommand):
    help = 'نمایش گرافیکی درخت باینری برای یک کاربر خاص'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='نام کاربری که می‌خواهید درختش را ببینید')
        parser.add_argument('--depth', type=int, default=3, help='عمق نمایش درخت (پیش‌فرض ۳ لایه)')

    def handle(self, *args, **options):
        username = options['username']
        max_depth = options['depth']

        try:
            root = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"کاربر {username} یافت نشد."))
            return

        self.stdout.write(self.style.WARNING(f"\nنمایش ساختار درختی برای: {root.username} (تا عمق {max_depth})\n"))
        self.print_tree(root, "", 0, max_depth)

    def print_tree(self, user, prefix, current_depth, max_depth):
        if current_depth > max_depth:
            return

        # نمادهای گرافیکی برای زیبایی
        connector = "└── " if prefix.endswith("    ") or prefix == "" else "├── "
        
        # رنگ‌آمیزی حجم‌ها
        vol_info = f"[L: {user.left_volume:,.0f} | R: {user.right_volume:,.0f}]"
        
        node_str = f"{user.username} {vol_info}"
        
        if current_depth == 0:
            self.stdout.write(self.style.SUCCESS(node_str))
        else:
            self.stdout.write(f"{prefix[:-4]}{connector}{node_str}")

        # پیدا کردن فرزندان
        left_child = User.objects.filter(binary_parent=user, binary_position='left').first()
        right_child = User.objects.filter(binary_parent=user, binary_position='right').first()

        new_prefix = prefix + "    "

        # بازگشتی برای فرزند چپ
        if left_child:
            self.stdout.write(f"{prefix}    Left:")
            self.print_tree(left_child, new_prefix, current_depth + 1, max_depth)
        elif current_depth < max_depth:
             self.stdout.write(f"{prefix}    Left: (Empty)")

        # بازگشتی برای فرزند راست
        if right_child:
            self.stdout.write(f"{prefix}    Right:")
            self.print_tree(right_child, new_prefix, current_depth + 1, max_depth)
        elif current_depth < max_depth:
             self.stdout.write(f"{prefix}    Right: (Empty)")
