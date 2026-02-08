"""
Wallet Models - مدل‌های مالی پروژه
تمام مدیریت موجودی‌ها، تراکنش‌ها و برداشت‌ها در این ماژول است
"""
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal


class Wallet(models.Model):
    """
    کیف پول کاربر - مدیریت متمرکز تمام موجودی‌ها
    
    Fields:
        - balance: موجودی نقدی (پول قابل برداشت)
        - investment_balance: موجودی سرمایه‌گذاری (سود ROI)
        - commission_balance: کمیسیون‌های دریافتی
        - locked_balance: موجودی قفل‌شده (در انتظار تایید برداشت)
    """
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wallet',
        verbose_name='کاربر'
    )
    
    # موجودی‌های مختلف
    balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='موجودی نقدی',
        help_text='موجودی قابل برداشت کاربر'
    )
    
    investment_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='موجودی سرمایه‌گذاری',
        help_text='سود حاصل از ROI که به موجودی نقدی منتقل می‌شود'
    )
    
    commission_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='موجودی کمیسیون',
        help_text='کمیسیون‌های دریافتی از سیستم باینری و سطوح'
    )
    
    locked_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='موجودی قفل‌شده',
        help_text='موجودی در انتظار تایید برداشت'
    )
    
    # تاریخ‌ها
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاریخ ایجاد'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاریخ آخرین بروزرسانی'
    )
    
    class Meta:
        db_table = 'wallets'
        verbose_name = 'کیف پول'
        verbose_name_plural = 'کیف پول‌ها'
        indexes = [
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"Wallet: {self.user.mobile}"
    
    @property
    def total_balance(self):
        """مجموع کل موجودی‌ها"""
        return self.balance + self.investment_balance + self.commission_balance
    
    @property
    def available_balance(self):
        """موجودی قابل استفاده (بدون قفل‌شده)"""
        return self.balance


class Transaction(models.Model):
    """
    تراکنش‌های مالی
    همه تراکنش‌های مالی سیستم در این مدل ثبت می‌شوند
    """
    
    TRANSACTION_TYPES = [
        ('deposit', 'واریز'),
        ('withdrawal', 'برداشت'),
        ('roi', 'سود روزانه'),
        ('commission_binary', 'کمیسیون باینری'),
        ('commission_level', 'کمیسیون سطح'),
        ('investment', 'سرمایه‌گذاری'),
        ('investment_return', 'بازگشت سرمایه'),
        ('refund', 'بازگشت وجه'),
        ('transfer', 'انتقال'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'در انتظار'),
        ('completed', 'تکمیل شده'),
        ('failed', 'ناموفق'),
        ('cancelled', 'لغو شده'),
    ]
    
    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name='کیف پول'
    )
    
    transaction_type = models.CharField(
        max_length=30,
        choices=TRANSACTION_TYPES,
        verbose_name='نوع تراکنش'
    )
    
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='مبلغ'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='وضعیت'
    )
    
    description = models.TextField(
        blank=True,
        verbose_name='توضیحات'
    )
    
    reference_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='شناسه مرجع',
        help_text='شناسه یکتا برای پیگیری تراکنش'
    )
    
    # اطلاعات اضافی (JSON)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='اطلاعات تکمیلی'
    )
    
    # تاریخ‌ها
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاریخ ایجاد'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاریخ بروزرسانی'
    )
    
    class Meta:
        db_table = 'transactions'
        verbose_name = 'تراکنش'
        verbose_name_plural = 'تراکنش‌ها'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['wallet', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['transaction_type', '-created_at']),
            models.Index(fields=['reference_id']),
        ]
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.amount} - {self.wallet.user.mobile}"


class WithdrawalRequest(models.Model):
    """
    درخواست‌های برداشت وجه
    مدیریت فرآیند برداشت از حساب کاربر
    """
    
    STATUS_CHOICES = [
        ('pending', 'در انتظار بررسی'),
        ('approved', 'تایید شده'),
        ('rejected', 'رد شده'),
        ('paid', 'پرداخت شده'),
        ('cancelled', 'لغو شده'),
    ]
    
    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name='withdrawal_requests',
        verbose_name='کیف پول'
    )
    
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('10000.00'))],
        verbose_name='مبلغ درخواست',
        help_text='حداقل مبلغ برداشت: 10,000 تومان'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='وضعیت'
    )
    
    # اطلاعات بانکی
    bank_name = models.CharField(
        max_length=100,
        verbose_name='نام بانک'
    )
    
    bank_account = models.CharField(
        max_length=20,
        verbose_name='شماره حساب',
        help_text='شماره حساب بانکی بدون خط تیره'
    )
    
    bank_card = models.CharField(
        max_length=16,
        blank=True,
        verbose_name='شماره کارت'
    )
    
    account_holder = models.CharField(
        max_length=100,
        verbose_name='نام صاحب حساب'
    )
    
    # توضیحات و یادداشت‌ها
    user_description = models.TextField(
        blank=True,
        verbose_name='توضیحات کاربر'
    )
    
    admin_note = models.TextField(
        blank=True,
        verbose_name='یادداشت مدیر'
    )
    
    rejection_reason = models.TextField(
        blank=True,
        verbose_name='دلیل رد درخواست'
    )
    
    # شناسه پرداخت
    payment_reference = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='شناسه پیگیری پرداخت'
    )
    
    # تاریخ‌ها
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاریخ درخواست'
    )
    
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاریخ پردازش'
    )
    
    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاریخ پرداخت'
    )
    
    class Meta:
        db_table = 'withdrawal_requests'
        verbose_name = 'درخواست برداشت'
        verbose_name_plural = 'درخواست‌های برداشت'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['wallet', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]
    
    def __str__(self):
        return f"Withdrawal {self.amount} - {self.wallet.user.mobile} - {self.get_status_display()}"
