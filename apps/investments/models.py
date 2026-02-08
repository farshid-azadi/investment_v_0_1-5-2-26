# apps/investments/models.py

from django.db import models
from django.conf import settings
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

class InvestmentPlan(models.Model):
    """
    مدل تعریف پلن‌های سرمایه‌گذاری
    """
    name = models.CharField(max_length=50)
    daily_interest_rate = models.DecimalField(max_digits=5, decimal_places=2, help_text="Daily ROI %")
    min_amount = models.DecimalField(max_digits=10, decimal_places=2)
    max_amount = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.IntegerField(default=30)
    description = models.TextField(blank=True, null=True)
    
# --- اضافه کردن تنظیمات روزهای پرداخت ---
    pay_on_monday = models.BooleanField(default=True, verbose_name="پرداخت در دوشنبه")
    pay_on_tuesday = models.BooleanField(default=True, verbose_name="پرداخت در سه‌شنبه")
    pay_on_wednesday = models.BooleanField(default=True, verbose_name="پرداخت در چهارشنبه")
    pay_on_thursday = models.BooleanField(default=True, verbose_name="پرداخت در پنج‌شنبه")
    pay_on_friday = models.BooleanField(default=True, verbose_name="پرداخت در جمعه")
    pay_on_saturday = models.BooleanField(default=True, verbose_name="پرداخت در شنبه") # معمولاً برای فارکس خاموش است
    pay_on_sunday = models.BooleanField(default=True, verbose_name="پرداخت در یکشنبه") # معمولاً برای فارکس خاموش است



    # --- فیلدهای جدید برای مدیریت ریسک و سقف درآمد ---
    max_total_return_percent = models.DecimalField(
        _("سقف کل برداشت (درصد)"),
        max_digits=6, decimal_places=2, default=250.00,
        help_text="حداکثر درصدی که کاربر می‌تواند از سرمایه خود برداشت کند (مثلا 250 درصد). بعد از این حد، پلن غیرفعال می‌شود."
    )
    binary_retention_days = models.IntegerField(
        _("مدت ذخیره حجم پای بلند (روز)"),
        default=30,
        help_text="مدت زمانی که حجم سمت قوی بدون تعادل باقی می‌ماند و پس از آن منقضی می‌شود."
    )
    # -------------------------------------------------

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.daily_interest_rate}%)"

class UserInvestment(models.Model):
    """
    سرمایه‌گذاری‌های کاربران با قابلیت Reinvest و کنترل سقف
    """
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('completed', 'Completed (Time Expired)'),
        ('capped', 'Completed (Max Cap Reached)'),
        ('cancelled', 'Cancelled'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='investments')
    plan_type = models.CharField(max_length=50, default='standard')

    # مبلغ اولیه خرید
    amount = models.DecimalField(max_digits=20, decimal_places=2, verbose_name="Initial Amount")

    # مبلغی که از طریق پاداش‌های شبکه (۵۰٪) اضافه شده است
    reinvested_amount = models.DecimalField(max_digits=20, decimal_places=2, default=0, verbose_name="Reinvested Capital")

    daily_interest_rate = models.DecimalField(max_digits=5, decimal_places=2, editable=False)
    
    # مجموع سود کسب شده از این سرمایه‌گذاری (برای کنترل سقف)
    total_profit_earned = models.DecimalField(max_digits=20, decimal_places=4, default=0)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # تاریخ پایان پلن
    end_date = models.DateTimeField(blank=True, null=True)
    duration_days = models.IntegerField(default=30)

    @property
    def active_capital(self):
        """
        محاسبه سرمایه فعال فعلی (اصل سرمایه + سودهای ری‌این‌وست شده)
        """
        # اگر مقادیر None بودند (مثلاً هنگام ایجاد آبجکت جدید)، صفر در نظر گرفته شوند
        current_amount = self.amount if self.amount is not None else 0
        current_reinvest = self.reinvested_amount if self.reinvested_amount is not None else 0
        
        return current_amount + current_reinvest
    def save(self, *args, **kwargs):
        is_new = self.pk is None

        # اگر رکورد جدید است، تنظیمات اولیه انجام شود
        if is_new:
            # 1. تنظیم تاریخ پایان
            if not self.end_date:
                # سعی میکنیم پلن را پیدا کنیم تا مدت زمان دقیق باشد
                try:
                    plan_obj = InvestmentPlan.objects.get(name=self.plan_type)
                    self.duration_days = plan_obj.duration_days
                    if not self.daily_interest_rate:
                        self.daily_interest_rate = plan_obj.daily_interest_rate
                except InvestmentPlan.DoesNotExist:
                    # Fallback defaults
                    pass

                self.end_date = timezone.now() + timezone.timedelta(days=self.duration_days)

            if not self.daily_interest_rate:
                 self.daily_interest_rate = Decimal('1.00') # Default fallback

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - Capital: {self.active_capital} - {self.status}"

class ReferralLevel(models.Model):
    """
    سطوح ارجاع برای پاداش مستقیم
    """
    level = models.PositiveIntegerField(unique=True, help_text="Level Number (1, 2, ...)")

    # پورسانت روی خرید مستقیم
    commission_percentage = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        help_text="Direct Invest Commission % (e.g. 5.000)"
    )

    class Meta:
        ordering = ['level']
        verbose_name = "Referral Level"
        verbose_name_plural = "Referral Levels"

    def __str__(self):
        return f"Level {self.level}: {self.commission_percentage}%"
