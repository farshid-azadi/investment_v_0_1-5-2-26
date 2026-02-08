# apps/accounts/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser
import random
import string
from decimal import Decimal
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.cache import cache

# --- مدل جدید برای لاگ کردن درآمدهای سوخت شده ---
class BurnedIncome(models.Model):
    """
    ذخیره درآمدهایی که به دلیل سقف روزانه یا سقف پلن سوخت شده‌اند.
    """
    REASON_CHOICES = (
        ('daily_cap', 'Daily Cap Exceeded'),
        ('total_cap', 'Total Plan Cap Reached'),
        ('no_active_plan', 'No Active Plan'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='burned_incomes',
        verbose_name="کاربر"
    )
    amount = models.DecimalField(_("مقدار سوخت شده"), max_digits=20, decimal_places=2)
    reason = models.CharField(_("دلیل"), max_length=20, choices=REASON_CHOICES)
    description = models.TextField(_("توضیحات تکمیلی"), blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "درآمد سوخت شده"
        verbose_name_plural = "لیست درآمدهای سوخت شده"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.amount} ({self.get_reason_display()})"

# -------------------------------------------------------------------------

class BinaryCommission(models.Model):
    """
    ذخیره تاریخچه دقیق کمیسیون‌های باینری شامل مبالغ پرداخت شده و سوخت شده.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="binary_commissions",
        verbose_name="کاربر"
    )

    matched_volume = models.DecimalField(
        max_digits=20, decimal_places=2,
        verbose_name="حجم تعادل (Match)",
        help_text="حجمی که در هر دو طرف وجود داشت و تسویه شد."
    )
    percentage = models.DecimalField(
        max_digits=5, decimal_places=2,
        verbose_name="درصد اعمال شده",
        default=0
    )

    # فیلدهای حیاتی برای گزارش‌گیری مالی
    calc_amount = models.DecimalField(
        max_digits=20, decimal_places=2,
        verbose_name="سود محاسباتی (خام)",
        help_text="سود کل قبل از اعمال سقف درآمد.",
        default=0
    )
    paid_amount = models.DecimalField(
        max_digits=20, decimal_places=2,
        verbose_name="سود پرداخت شده",
        help_text="مبلغ نهایی واریز شده به کیف پول."
    )
    flushed_amount = models.DecimalField(
        max_digits=20, decimal_places=2,
        verbose_name="سود سوخت شده (Flush)",
        help_text="🔥 مبلغی که به دلیل سقف درآمد روزانه به کاربر تعلق نگرفت.",
        default=0
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ محاسبه")

    def __str__(self):
        return f"{self.user} - پرداخت: {self.paid_amount}"

    class Meta:
        verbose_name = "گزارش کمیسیون باینری"
        verbose_name_plural = "گزارشات کمیسیون باینری"
        ordering = ['-created_at']

class User(AbstractUser):
    # -------------------------------------------------------------------------
    # اطلاعات پایه و احراز هویت
    # -------------------------------------------------------------------------
    mobile = models.CharField(
        max_length=15,
        unique=True,
        null=True,   
        blank=True,  
        verbose_name="شماره موبایل",
        help_text="مثال: 09123456789"
    )

    referral_code = models.CharField(
        max_length=10,
        unique=True,
        blank=True,
        null=True,
        verbose_name="کد معرف اختصاصی",
        help_text="کدی که این کاربر برای دعوت دیگران استفاده می‌کند (فقط بعد از سرمایه‌گذاری تولید می‌شود)."
    )

    referrer = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='referrals',
        verbose_name="معرف مستقیم (Direct)",
        help_text="شخصی که این کاربر را مستقیماً دعوت کرده است."
    )

    # -------------------------------------------------------------------------
    # سیستم مالی
    # -------------------------------------------------------------------------
    cash_balance = models.DecimalField(
        default=0,
        max_digits=20,
        decimal_places=2,
        verbose_name="موجودی نقدی (قابل برداشت)",
        help_text="موجودی دلاری که کاربر می‌تواند درخواست برداشت دهد."
    )

    reinvest_balance = models.DecimalField(
        default=0,
        max_digits=20,
        decimal_places=2,
        verbose_name="موجودی سرمایه‌گذاری مجدد",
        help_text="موجودی که فقط برای خرید پلن قابل استفاده است."
    )

    # -------------------------------------------------------------------------
    # کریپتو و لاتاری
    # -------------------------------------------------------------------------
    crypto_wallet_address = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        unique=True,
        verbose_name="آدرس کیف پول تتر (واریز)",
        help_text="آدرس اختصاصی تولید شده برای واریزهای کاربر."
    )
    crypto_address_index = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="ایندکس HD Wallet",
        help_text="⚠️ فنی: شماره ردیف در کیف پول مادر. دستی تغییر ندهید."
    )

    lottery_points = models.IntegerField(
        default=0,
        verbose_name="امتیاز لاتاری"
    )

    auto_compound = models.BooleanField(
        default=False,
        verbose_name="سود مرکب خودکار (Auto Compound)",
        help_text="اگر فعال باشد، سود روزانه به جای کیف پول، به اصل سرمایه اضافه می‌شود."
    )

    # -------------------------------------------------------------------------
    # سیستم باینری
    # -------------------------------------------------------------------------
    binary_parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='binary_children',
        verbose_name=("والد باینری")
    )
    binary_position = models.CharField(
        max_length=10,
        choices=(('left', 'Left'), ('right', 'Right')),
        null=True, blank=True
    )

    left_volume = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=0,
        verbose_name="حجم فروش سمت چپ",
        help_text="امتیازهای جمع شده در تیم چپ (هنوز تسویه نشده)."
    )

    right_volume = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=0,
        verbose_name="حجم فروش سمت راست",
        help_text="امتیازهای جمع شده در تیم راست (هنوز تسویه نشده)."
    )

    total_commission_earned = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=0,
        verbose_name="کل درآمد کسب شده",
        help_text="مجموع تمام کمیسیون‌های دریافتی تا این لحظه."
    )

    # فیلد قدیمی برای سازگاری
    balance = models.DecimalField(
        max_digits=20, decimal_places=2, default=0,
        verbose_name="تراز کل (Legacy)"
    )

    class Meta:
        verbose_name = "کاربر"
        verbose_name_plural = "کاربران"

    def __str__(self):
        return f"{self.username} ({self.first_name} {self.last_name})"

    # نکته: متد generate_unique_referral_code از save حذف شده تا کد هنگام ثبت نام ساخته نشود.
    
    def is_binary_active(self):
        # بررسی می‌کند آیا کاربر سرمایه‌گذاری فعال دارد
        return self.investments.filter(status='active').exists()
    is_binary_active.boolean = True
    is_binary_active.short_description = "وضعیت باینری"

class UserPlan(models.Model):
    """
    پلن فعال کاربر (مدل قدیمی‌تر که برای سازگاری نگه داشته شده)
    """
    user = models.OneToOneField(
        "User",
        on_delete=models.CASCADE,
        related_name="active_plan",
        verbose_name="کاربر"
    )

    plan = models.ForeignKey(
        "investments.InvestmentPlan", # ارتباط با مدل جدید پلن‌ها
        on_delete=models.PROTECT,
        verbose_name="پلن انتخابی"
    )

    principal_amount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=0,
        verbose_name="مبلغ اصل سرمایه"
    )

    accumulated_profit = models.DecimalField(
        default=0,
        max_digits=20,
        decimal_places=2,
        verbose_name="سود انباشته شده"
    )

    activated_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ فعال‌سازی")
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ انقضا")
    is_active = models.BooleanField(default=True, verbose_name="فعال است؟")

    def __str__(self):
        return f"{self.user} - {self.plan}"

    class Meta:
        verbose_name = "پلن فعال کاربر"
        verbose_name_plural = "پلن‌های فعال کاربران"

class LevelCommissionHistory(models.Model):
    earner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="level_commissions",
        verbose_name="دریافت کننده"
    )
    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="generated_level_commissions",
        verbose_name="بابت کاربر (منشاء)"
    )
    level = models.PositiveIntegerField(verbose_name="سطح (Level)")
    amount = models.DecimalField(max_digits=20, decimal_places=2, verbose_name="مبلغ پورسانت")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ واریز")

    class Meta:
        indexes = [
            models.Index(fields=["earner", "created_at"])
        ]
        verbose_name = "تاریخچه کمیسیون سطحی"
        verbose_name_plural = "تاریخچه کمیسیون‌های سطحی"

class ROIHistory(models.Model):
    """
    تاریخچه سود روزانه
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="roi_histories",
        verbose_name="کاربر"
    )
    plan = models.ForeignKey(
        "investments.InvestmentPlan",
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="پلن مرتبط"
    )

    amount = models.DecimalField(max_digits=20, decimal_places=2, verbose_name="مبلغ سود")
    percent = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="درصد اعمال شده")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ واریز")

    class Meta:
        indexes = [
            models.Index(fields=["user", "created_at"]),
        ]
        verbose_name = "تاریخچه سود روزانه (ROI)"
        verbose_name_plural = "تاریخچه سودهای روزانه"

    def __str__(self):
        return f"{self.user} - ROI: {self.amount}"

class RegistrationSettings(models.Model):
    is_referral_required = models.BooleanField(default=True, verbose_name="کد معرف اجباری باشد")
    is_email_required = models.BooleanField(default=False, verbose_name="ایمیل اجباری باشد")
    is_mobile_required = models.BooleanField(default=True, verbose_name="موبایل اجباری باشد")
    
    class Meta:
        verbose_name = "تنظیمات ثبت نام"
        verbose_name_plural = "تنظیمات ثبت نام"

    def save(self, *args, **kwargs):
        # جلوگیری از ایجاد رکورد دوم
        if not self.pk and RegistrationSettings.objects.exists():
            # اگر رکوردی هست، روی همان آپدیت کن
            self.pk = RegistrationSettings.objects.first().pk
        super().save(*args, **kwargs)
        # پاک کردن کش برای اعمال سریع تغییرات
        cache.delete('registration_settings')

    def __str__(self):
        return "تنظیمات کلی ثبت نام"

    @classmethod
    def load(cls):
        """متدی برای دریافت سریع تنظیمات (با استفاده از کش)"""
        settings = cache.get('registration_settings')
        if settings is None:
            settings, created = cls.objects.get_or_create(pk=1)
            cache.set('registration_settings', settings, 60*60) # کش برای یک ساعت
        return settings

# apps/accounts/models.py
# ... کدهای قبلی موجود ...

# ============================================================================
# 💳 Payment Request Model (اضافه شده در 1404/10/17)
# ============================================================================

class PaymentRequest(models.Model):
    """
    درخواست واریز کاربر - مرحله قبل از تبدیل به Investment
    
    جریان کار:
    1. کاربر درخواست ایجاد می‌کند (status=pending)
    2. ادمین مبلغ را تأیید می‌کند (verified_amount)
    3. ادمین status را approved می‌کند
    4. Signal خودکار Investment می‌سازد
    """
    
    CURRENCY_CHOICES = (
        ('USDT', 'Tether (USDT-TRC20)'),
        ('BTC', 'Bitcoin'),
        ('ETH', 'Ethereum'),
        ('TRX', 'Tron'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'در انتظار بررسی'),
        ('approved', 'تأیید شده'),
        ('rejected', 'رد شده'),
    )

    # -------------------------------------------------------------------------
    # فیلدهای کاربر (User Input)
    # -------------------------------------------------------------------------
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payment_requests',
        verbose_name="کاربر"
    )
    
    plan = models.ForeignKey(
        'investments.InvestmentPlan',
        on_delete=models.PROTECT,
        verbose_name="پلن انتخابی",
        help_text="پلنی که کاربر قصد خرید آن را دارد"
    )
    
    currency = models.CharField(
        max_length=10,
        choices=CURRENCY_CHOICES,
        default='USDT',
        verbose_name="نوع ارز پرداختی"
    )
    
    txid_or_hash = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Transaction ID / Hash",
        help_text="کد تراکنش از بلاکچین (اختیاری)"
    )
    
    receipt_image = models.ImageField(
        upload_to='payment_receipts/%Y/%m/%d/',
        blank=True,
        null=True,
        verbose_name="تصویر رسید پرداخت",
        help_text="اسکرین‌شات از تراکنش یا رسید بانکی"
    )
    
    # -------------------------------------------------------------------------
    # فیلدهای ادمین (Admin Only)
    # -------------------------------------------------------------------------
    verified_amount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="💰 مبلغ تأیید شده (USD)",
        help_text="⚠️ ادمین: مبلغ واقعی دریافتی را وارد کنید"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="وضعیت درخواست",
        db_index=True
    )
    
    admin_notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="یادداشت ادمین (داخلی)",
        help_text="توضیحات برای سایر ادمین‌ها (کاربر نمی‌بیند)"
    )
    
    # -------------------------------------------------------------------------
    # فیلدهای زمان و ارتباط
    # -------------------------------------------------------------------------
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="تاریخ ایجاد درخواست"
    )
    
    processed_at = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name="تاریخ بررسی ادمین"
    )
    
    related_investment = models.OneToOneField(
        'investments.UserInvestment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payment_source',
        verbose_name="سرمایه‌گذاری ایجاد شده",
        help_text="🔗 لینک به Investment که از این Payment ساخته شد"
    )
    
    class Meta:
        verbose_name = "💳 درخواست واریز"
        verbose_name_plural = "💳 درخواست‌های واریز"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        status_emoji = {
            'pending': '⏳',
            'approved': '✅',
            'rejected': '❌'
        }
        emoji = status_emoji.get(self.status, '❓')
        amount_str = f"${self.verified_amount:,.2f}" if self.verified_amount else "بدون مبلغ"
        return f"{emoji} {self.user.username} - {self.plan.name} - {amount_str}"
    
    def save(self, *args, **kwargs):
        """ثبت خودکار زمان بررسی"""
        if self.status in ['approved', 'rejected'] and not self.processed_at:
            from django.utils import timezone
            self.processed_at = timezone.now()
        super().save(*args, **kwargs)
    
    @property
    def is_pending(self):
        return self.status == 'pending'
    
    @property
    def can_be_approved(self):
        """چک می‌کند آیا قابل تأیید است"""
        return (
            self.status == 'pending' and 
            self.verified_amount and 
            self.verified_amount > 0 and
            not self.related_investment  # قبلاً Investment نساخته باشد
        )
