# apps/accounts/management/commands/setup_scheduled_tasks.py

from django.core.management.base import BaseCommand
from django_q.models import Schedule


class Command(BaseCommand):
    help = "⏰ تنظیم Scheduled Tasks برای پرداخت ROI و Binary Flush"

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("🔄 در حال تنظیم Scheduled Tasks..."))

        # -----------------------------------------------------------------------
        # Task 1: پرداخت سود روزانه (ROI) - هر روز ساعت 00:01
        # -----------------------------------------------------------------------
        roi_schedule, created = Schedule.objects.update_or_create(
            name='daily_roi_payment',
            defaults={
                'func': 'apps.accounts.tasks.process_all_daily_roi',
                'schedule_type': Schedule.CRON,
                'cron': '1 0 * * *',  # هر روز ساعت 00:01
                'repeats': -1,  # بی‌نهایت تکرار
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f"✅ Task جدید ایجاد شد: {roi_schedule.name}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"♻️ Task به‌روزرسانی شد: {roi_schedule.name}"))

        # -----------------------------------------------------------------------
        # Task 2: تسویه باینری (Binary Flush) - هر یکشنبه ساعت 02:00
        # -----------------------------------------------------------------------
        binary_schedule, created = Schedule.objects.update_or_create(
            name='weekly_binary_flush',
            defaults={
                'func': 'apps.accounts.tasks.process_all_binary_flush',
                'schedule_type': Schedule.CRON,
                'cron': '0 2 * * 0',  # هر یکشنبه ساعت 02:00
                'repeats': -1,
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f"✅ Task جدید ایجاد شد: {binary_schedule.name}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"♻️ Task به‌روزرسانی شد: {binary_schedule.name}"))

        self.stdout.write(self.style.SUCCESS("\n🎉 همه Scheduled Tasks با موفقیت تنظیم شدند!"))
        self.stdout.write(self.style.WARNING("\n⚠️ برای اجرای Scheduleها، Worker را با دستور زیر اجرا کنید:"))
        self.stdout.write(self.style.HTTP_INFO("   python manage.py qcluster\n"))

