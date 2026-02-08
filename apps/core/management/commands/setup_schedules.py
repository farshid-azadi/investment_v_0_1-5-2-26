"""
Management Command: تنظیم Scheduled Tasks در Django-Q2
استفاده: python manage.py setup_schedules
"""
from django.core.management.base import BaseCommand
from django_q.models import Schedule


class Command(BaseCommand):
    help = 'تنظیم وظایف زمان‌بندی شده در Django-Q2'
    
    def handle(self, *args, **options):
        """ایجاد یا بروزرسانی Scheduled Tasks"""
        
        schedules = [
            {
                'name': 'پردازش سود روزانه (ROI)',
                'func': 'apps.investments.tasks.process_daily_roi',
                'schedule_type': Schedule.CRON,
                'cron': '0 0 * * *',  # هر روز ساعت 00:00
                'repeats': -1,  # بی‌نهایت
            },
            {
                'name': 'محاسبه کمیسیون باینری روزانه',
                'func': 'apps.accounts.tasks.calculate_binary_commissions',
                'schedule_type': Schedule.CRON,
                'cron': '30 0 * * *',  # هر روز ساعت 00:30
                'repeats': -1,
            },
            {
                'name': 'پاکسازی تراکنش‌های قدیمی',
                'func': 'apps.wallet.tasks.cleanup_old_transactions',
                'schedule_type': Schedule.CRON,
                'cron': '0 3 1 * *',  # اول هر ماه ساعت 03:00
                'repeats': -1,
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for schedule_data in schedules:
            name = schedule_data.pop('name')
            
            schedule, created = Schedule.objects.update_or_create(
                name=name,
                defaults=schedule_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✅ ایجاد شد: {name}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'🔄 بروزرسانی شد: {name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n📊 خلاصه: {created_count} ایجاد، {updated_count} بروزرسانی'
            )
        )
        
        # نمایش لیست همه Schedules
        self.stdout.write('\n📋 لیست کامل Scheduled Tasks:')
        for schedule in Schedule.objects.all():
            self.stdout.write(
                f'  - {schedule.name} ({schedule.get_schedule_type_display()})'
            )
