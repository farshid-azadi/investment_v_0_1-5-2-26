"""
apps/core/models.py

مدل‌های اصلی و تنظیمات سیستم MLM
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal


class Plan(models.Model):
    """
    پلن‌های سرمایه‌گذاری
    هر پلن شامل تنظیمات جداگانه برای باینری و ROI است
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="نام پلن"
    )
    
    price = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="قیمت پلن (USDT)"
    )
    
    # ─────────────────────────────────────────────────────────
    # تنظیمات باینری مخصوص این پلن
    # ─────────────────────────────────────────────────────────
    binary_volume = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="حجم باینری تولیدی",
        help_text="حجمی که این پلن در ساختار باینری والد تولید می‌کند"
    )
    
    binary_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[
            MinValueValidator(Decimal('0')),
            MaxValueValidator(Decimal('100'))
        ],
        verbose_name="درصد کمیسیون باینری",
        help_text="اگر 0 باشد، از تنظیمات کلی MLM استفاده می‌شود"
    )
    
    daily_binary_cap = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="سقف سود روزانه باینری",
        help_text="حداکثر سود باینری قابل دریافت در روز (0 = نامحدود)"
    )
    
    # ─────────────────────────────────────────────────────────
    # تنظیمات ROI (Return on Investment)
    # ─────────────────────────────────────────────────────────
    roi_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[
            MinValueValidator(Decimal('0')),
            MaxValueValidator(Decimal('100'))
        ],
        verbose_name="درصد سود ماهیانه ROI",
        help_text="سود ثابت ماهیانه (0 = بدون ROI)"
    )
    
    roi_duration_days = models.PositiveIntegerField(
        default=365,
        verbose_name="مدت زمان ROI (روز)",
        help_text="تعداد روزهایی که ROI پرداخت می‌شود"
    )
    
    # ─────────────────────────────────────────────────────────
    # وضعیت و نمایش
    # ─────────────────────────────────────────────────────────
    is_active = models.BooleanField(
        default=True,
        verbose_name="فعال"
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="توضیحات"
    )
    
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="ترتیب نمایش"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "پلن سرمایه‌گذاری"
        verbose_name_plural = "پلن‌های سرمایه‌گذاری"
        ordering = ['order', 'price']
        indexes = [
            models.Index(fields=['is_active', 'price']),
        ]

    def __str__(self):
        return f"{self.name} - ${self.price}"
    
    def clean(self):
        """اعتبارسنجی داده‌ها"""
        super().clean()
        
        if self.binary_percentage > 0 and self.binary_volume == 0:
            raise ValidationError({
                'binary_volume': 'اگر درصد باینری تنظیم شده، حجم باینری نباید صفر باشد'
            })
        
        if self.roi_percent > 0 and self.roi_duration_days == 0:
            raise ValidationError({
                'roi_duration_days': 'اگر ROI فعال است، مدت زمان نباید صفر باشد'
            })
    
    def get_effective_binary_percentage(self):
        """
        درصد باینری مؤثر (یا از پلن یا از تنظیمات کلی)
        """
        if self.binary_percentage > 0:
            return self.binary_percentage
        
        # استفاده از تنظیمات کلی
        try:
            mlm_settings = MLMSettings.get_solo()
            return mlm_settings.binary_percentage
        except:
            return Decimal('10.00')  # مقدار پیش‌فرض
    
    def calculate_daily_roi(self):
        """
        محاسبه سود روزانه ROI
        """
        if self.roi_percent == 0 or self.roi_duration_days == 0:
            return Decimal('0.00')
        
        monthly_roi = (self.price * self.roi_percent) / 100
        daily_roi = monthly_roi / 30  # تقسیم به 30 روز
        
        return daily_roi.quantize(Decimal('0.01'))


class LevelCommissionSetting(models.Model):
    """
    تنظیمات کمیسیون سطح‌بندی (Level/Unilevel)
    هر سطح درصد کمیسیون خاص خود را دارد
    """
    level = models.PositiveIntegerField(
        unique=True,
        validators=[MinValueValidator(1)],
        verbose_name="شماره سطح"
    )
    
    percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal('0')),
            MaxValueValidator(Decimal('100'))
        ],
        verbose_name="درصد کمیسیون"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="فعال"
    )
    
    description = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="توضیحات"
    )

    class Meta:
        verbose_name = "تنظیمات کمیسیون سطح"
        verbose_name_plural = "تنظیمات کمیسیون سطوح"
        ordering = ['level']
        indexes = [
            models.Index(fields=['level', 'is_active']),
        ]

    def __str__(self):
        return f"سطح {self.level} - {self.percent}%"
    
    @classmethod
    def get_percent_for_level(cls, level: int) -> Decimal:
        """
        دریافت درصد کمیسیون برای یک سطح خاص
        """
        try:
            setting = cls.objects.get(level=level, is_active=True)
            return setting.percent
        except cls.DoesNotExist:
            return Decimal('0.00')


class WithdrawalSetting(models.Model):
    """
    تنظیمات برداشت وجه (سینگلتون - فقط یک رکورد)
    """
    min_withdrawal_amount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal('10.00'),
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="حداقل مبلغ برداشت"
    )
    
    max_withdrawal_amount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal('10000.00'),
        validators=[MinValueValidator(Decimal('1.00'))],
        verbose_name="حداکثر مبلغ برداشت (در هر درخواست)"
    )
    
    withdrawal_fee_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('3.00'),
        validators=[
            MinValueValidator(Decimal('0')),
            MaxValueValidator(Decimal('100'))
        ],
        verbose_name="درصد کارمزد برداشت"
    )
    
    withdrawal_fee_fixed = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="کارمزد ثابت برداشت",
        help_text="علاوه بر درصد، یک مبلغ ثابت نیز کسر می‌شود"
    )
    
    daily_withdrawal_limit = models.PositiveIntegerField(
        default=3,
        verbose_name="محدودیت تعداد برداشت روزانه",
        help_text="0 = نامحدود"
    )
    
    auto_approve_threshold = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="آستانه تأیید خودکار",
        help_text="درخواست‌های زیر این مبلغ به صورت خودکار تأیید می‌شوند (0 = غیرفعال)"
    )
    
    withdrawal_processing_days = models.PositiveIntegerField(
        default=3,
        verbose_name="مدت زمان پردازش برداشت (روز کاری)"
    )

    class Meta:
        verbose_name = "تنظیمات برداشت"
        verbose_name_plural = "تنظیمات برداشت"

    def __str__(self):
        return "تنظیمات برداشت وجه"

    def save(self, *args, **kwargs):
        """
        اطمینان از وجود فقط یک رکورد (Singleton Pattern)
        """
        if not self.pk and WithdrawalSetting.objects.exists():
            # اگر رکوردی وجود دارد، آن را بروزرسانی کن
            existing = WithdrawalSetting.objects.first()
            self.pk = existing.pk
        super().save(*args, **kwargs)
    
    def clean(self):
        """اعتبارسنجی"""
        super().clean()
        
        if self.min_withdrawal_amount > self.max_withdrawal_amount:
            raise ValidationError({
                'min_withdrawal_amount': 'حداقل برداشت نباید بیشتر از حداکثر باشد'
            })
    
    def calculate_fee(self, amount: Decimal) -> Decimal:
        """
        محاسبه کارمزد برای یک مبلغ
        Returns: (fee, payable_amount)
        """
        percentage_fee = (amount * self.withdrawal_fee_percentage) / 100
        total_fee = percentage_fee + self.withdrawal_fee_fixed
        payable_amount = amount - total_fee
        
        return total_fee.quantize(Decimal('0.01'))
    
    @classmethod
    def get_solo(cls):
        """دریافت تنها رکورد (ایجاد در صورت عدم وجود)"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class MLMSettings(models.Model):
    """
    تنظیمات کلی سیستم MLM (سینگلتون)
    """
    # ─────────────────────────────────────────────────────────
    # تنظیمات باینری
    # ─────────────────────────────────────────────────────────
    binary_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('10.00'),
        validators=[
            MinValueValidator(Decimal('0')),
            MaxValueValidator(Decimal('100'))
        ],
        verbose_name="درصد کمیسیون باینری پیش‌فرض",
        help_text="برای پلن‌هایی که درصد مخصوص ندارند"
    )
    
    binary_match_type = models.CharField(
        max_length=20,
        choices=[
            ('weak_leg', 'پای ضعیف (Weak Leg)'),
            ('both_legs', 'هر دو پا'),
        ],
        default='weak_leg',
        verbose_name="نوع محاسبه باینری"
    )
    
    binary_carry_forward = models.BooleanField(
        default=True,
        verbose_name="انتقال حجم اضافی به روز بعد",
        help_text="آیا حجم باقیمانده به روز بعد منتقل شود؟"
    )
    
    # ─────────────────────────────────────────────────────────
    # تنظیمات سطح‌بندی
    # ─────────────────────────────────────────────────────────
    max_level_depth = models.PositiveIntegerField(
        default=10,
        validators=[MinValueValidator(1)],
        verbose_name="حداکثر عمق سطح‌بندی",
        help_text="تا چند سطح به بالا کمیسیون پرداخت شود"
    )
    
    level_commission_from = models.CharField(
        max_length=20,
        choices=[
            ('plan_price', 'قیمت پلن'),
            ('binary_commission', 'کمیسیون باینری'),
        ],
        default='plan_price',
        verbose_name="پایه محاسبه کمیسیون سطح",
        help_text="کمیسیون سطح از کدام مبلغ محاسبه شود"
    )
    
    # ─────────────────────────────────────────────────────────
    # تنظیمات ROI
    # ─────────────────────────────────────────────────────────
    roi_payment_time = models.TimeField(
        default='00:00:00',
        verbose_name="ساعت پرداخت ROI روزانه"
    )
    
    roi_payment_on_weekends = models.BooleanField(
        default=True,
        verbose_name="پرداخت ROI در تعطیلات",
        help_text="آیا ROI در روزهای شنبه و جمعه پرداخت شود؟"
    )
    
    # ─────────────────────────────────────────────────────────
    # سایر تنظیمات
    # ─────────────────────────────────────────────────────────
    maintenance_mode = models.BooleanField(
        default=False,
        verbose_name="حالت تعمیرات",
        help_text="در این حالت کاربران نمی‌توانند خرید/برداشت انجام دهند"
    )
    
    maintenance_message = models.TextField(
        blank=True,
        null=True,
        verbose_name="پیام حالت تعمیرات"
    )
    
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "تنظیمات MLM"
        verbose_name_plural = "تنظیمات MLM"

    def __str__(self):
        return "تنظیمات کلی سیستم MLM"

    def save(self, *args, **kwargs):
        """Singleton Pattern"""
        if not self.pk and MLMSettings.objects.exists():
            existing = MLMSettings.objects.first()
            self.pk = existing.pk
        super().save(*args, **kwargs)
    
    @classmethod
    def get_solo(cls):
        """دریافت تنها رکورد"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


# ────────────────────────────────────────────────────────────────────
# نکته مهم:
# مدل‌های Transaction و WithdrawalRequest در apps/wallet/models.py قرار دارند
# این تفکیک برای معماری بهتر و جلوگیری از وابستگی دایره‌ای است
# ────────────────────────────────────────────────────────────────────
