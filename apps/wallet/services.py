"""
Wallet Service - سرویس مدیریت Wallet
این سرویس تمام عملیات مالی را با Transaction Safety مدیریت می‌کند
"""
from decimal import Decimal
from typing import Optional
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.wallet.models import Wallet, Transaction


class WalletService:
    """
    سرویس مدیریت Wallet با امنیت تراکنش
    
    تمام متدها از select_for_update() برای جلوگیری از
    Race Condition و atomic() برای یکپارچگی تراکنش استفاده می‌کنند.
    """
    
    @staticmethod
    @transaction.atomic
    def credit_balance(
        wallet_id: int,
        amount: Decimal,
        transaction_type: str,
        description: str = "",
        reference_id: str = "",
        metadata: dict = None
    ) -> Wallet:
        """
        افزایش موجودی نقدی (balance)
        
        Args:
            wallet_id: شناسه کیف پول
            amount: مبلغ (باید مثبت باشد)
            transaction_type: نوع تراکنش
            description: توضیحات
            reference_id: شناسه مرجع
            metadata: اطلاعات اضافی
        
        Returns:
            Wallet: کیف پول بروزرسانی شده
        
        Raises:
            ValidationError: اگر مبلغ منفی باشد
        """
        if amount <= 0:
            raise ValidationError("مبلغ باید مثبت باشد")
        
        # قفل کردن رکورد Wallet برای جلوگیری از Race Condition
        wallet = Wallet.objects.select_for_update().get(id=wallet_id)
        
        # افزایش موجودی
        wallet.balance += amount
        wallet.save()
        
        # ثبت تراکنش
        Transaction.objects.create(
            wallet=wallet,
            transaction_type=transaction_type,
            amount=amount,
            status='completed',
            description=description,
            reference_id=reference_id,
            metadata=metadata or {}
        )
        
        return wallet
    
    @staticmethod
    @transaction.atomic
    def debit_balance(
        wallet_id: int,
        amount: Decimal,
        transaction_type: str,
        description: str = "",
        reference_id: str = "",
        metadata: dict = None
    ) -> Wallet:
        """
        کاهش موجودی نقدی (balance)
        
        Args:
            wallet_id: شناسه کیف پول
            amount: مبلغ (باید مثبت باشد)
            transaction_type: نوع تراکنش
            description: توضیحات
            reference_id: شناسه مرجع
            metadata: اطلاعات اضافی
        
        Returns:
            Wallet: کیف پول بروزرسانی شده
        
        Raises:
            ValidationError: اگر موجودی کافی نباشد یا مبلغ منفی باشد
        """
        if amount <= 0:
            raise ValidationError("مبلغ باید مثبت باشد")
        
        # قفل کردن رکورد
        wallet = Wallet.objects.select_for_update().get(id=wallet_id)
        
        # بررسی کفایت موجودی
        if wallet.balance < amount:
            raise ValidationError(
                f"موجودی کافی نیست. موجودی فعلی: {wallet.balance}, مبلغ درخواستی: {amount}"
            )
        
        # کاهش موجودی
        wallet.balance -= amount
        wallet.save()
        
        # ثبت تراکنش
        Transaction.objects.create(
            wallet=wallet,
            transaction_type=transaction_type,
            amount=amount,
            status='completed',
            description=description,
            reference_id=reference_id,
            metadata=metadata or {}
        )
        
        return wallet
    
    @staticmethod
    @transaction.atomic
    def credit_investment_balance(
        wallet_id: int,
        amount: Decimal,
        description: str = "سود روزانه",
        reference_id: str = "",
        metadata: dict = None
    ) -> Wallet:
        """
        افزایش موجودی سرمایه‌گذاری (ROI)
        
        این متد برای ثبت سود روزانه استفاده می‌شود
        """
        if amount <= 0:
            raise ValidationError("مبلغ باید مثبت باشد")
        
        wallet = Wallet.objects.select_for_update().get(id=wallet_id)
        
        wallet.investment_balance += amount
        wallet.save()
        
        Transaction.objects.create(
            wallet=wallet,
            transaction_type='roi',
            amount=amount,
            status='completed',
            description=description,
            reference_id=reference_id,
            metadata=metadata or {}
        )
        
        return wallet
    
    @staticmethod
    @transaction.atomic
    def transfer_investment_to_balance(
        wallet_id: int,
        amount: Optional[Decimal] = None
    ) -> Wallet:
        """
        انتقال موجودی سرمایه‌گذاری به موجودی نقدی
        
        Args:
            wallet_id: شناسه کیف پول
            amount: مبلغ (اگر None باشد، کل موجودی منتقل می‌شود)
        
        Returns:
            Wallet: کیف پول بروزرسانی شده
        """
        wallet = Wallet.objects.select_for_update().get(id=wallet_id)
        
        # تعیین مبلغ انتقال
        transfer_amount = amount if amount is not None else wallet.investment_balance
        
        if transfer_amount <= 0:
            raise ValidationError("مبلغ انتقال باید مثبت باشد")
        
        if wallet.investment_balance < transfer_amount:
            raise ValidationError("موجودی سرمایه‌گذاری کافی نیست")
        
        # انتقال موجودی
        wallet.investment_balance -= transfer_amount
        wallet.balance += transfer_amount
        wallet.save()
        
        # ثبت تراکنش
        Transaction.objects.create(
            wallet=wallet,
            transaction_type='transfer',
            amount=transfer_amount,
            status='completed',
            description='انتقال سود به موجودی نقدی'
        )
        
        return wallet
    
    @staticmethod
    @transaction.atomic
    def credit_commission(
        wallet_id: int,
        amount: Decimal,
        commission_type: str,
        description: str = "",
        reference_id: str = "",
        metadata: dict = None
    ) -> Wallet:
        """
        افزایش موجودی کمیسیون
        
        Args:
            wallet_id: شناسه کیف پول
            amount: مبلغ کمیسیون
            commission_type: نوع کمیسیون ('commission_binary' یا 'commission_level')
            description: توضیحات
            reference_id: شناسه مرجع
            metadata: اطلاعات اضافی
        """
        if amount <= 0:
            raise ValidationError("مبلغ باید مثبت باشد")
        
        wallet = Wallet.objects.select_for_update().get(id=wallet_id)
        
        wallet.commission_balance += amount
        wallet.save()
        
        Transaction.objects.create(
            wallet=wallet,
            transaction_type=commission_type,
            amount=amount,
            status='completed',
            description=description,
            reference_id=reference_id,
            metadata=metadata or {}
        )
        
        return wallet
    
    @staticmethod
    @transaction.atomic
    def lock_balance(wallet_id: int, amount: Decimal) -> Wallet:
        """
        قفل کردن موجودی (برای برداشت)
        
        موجودی از balance به locked_balance منتقل می‌شود
        """
        if amount <= 0:
            raise ValidationError("مبلغ باید مثبت باشد")
        
        wallet = Wallet.objects.select_for_update().get(id=wallet_id)
        
        if wallet.balance < amount:
            raise ValidationError("موجودی کافی برای قفل کردن وجود ندارد")
        
        wallet.balance -= amount
        wallet.locked_balance += amount
        wallet.save()
        
        return wallet
    
    @staticmethod
    @transaction.atomic
    def unlock_balance(wallet_id: int, amount: Decimal) -> Wallet:
        """
        آزاد کردن موجودی قفل‌شده (رد درخواست برداشت)
        
        موجودی از locked_balance به balance برمی‌گردد
        """
        if amount <= 0:
            raise ValidationError("مبلغ باید مثبت باشد")
        
        wallet = Wallet.objects.select_for_update().get(id=wallet_id)
        
        if wallet.locked_balance < amount:
            raise ValidationError("موجودی قفل‌شده کافی نیست")
        
        wallet.locked_balance -= amount
        wallet.balance += amount
        wallet.save()
        
        return wallet
    
    @staticmethod
    @transaction.atomic
    def complete_withdrawal(wallet_id: int, amount: Decimal) -> Wallet:
        """
        تکمیل برداشت (کاهش locked_balance)
        
        پس از پرداخت واقعی به کاربر، موجودی قفل‌شده کاهش می‌یابد
        """
        if amount <= 0:
            raise ValidationError("مبلغ باید مثبت باشد")
        
        wallet = Wallet.objects.select_for_update().get(id=wallet_id)
        
        if wallet.locked_balance < amount:
            raise ValidationError("موجودی قفل‌شده کافی نیست")
        
        wallet.locked_balance -= amount
        wallet.save()
        
        Transaction.objects.create(
            wallet=wallet,
            transaction_type='withdrawal',
            amount=amount,
            status='completed',
            description='برداشت وجه'
        )
        
        return wallet
    
    @staticmethod
    def get_wallet_by_user(user_id: int) -> Wallet:
        """دریافت Wallet بر اساس شناسه کاربر"""
        return Wallet.objects.select_related('user').get(user_id=user_id)
    
    @staticmethod
    def get_wallet_balance(wallet_id: int) -> dict:
        """دریافت اطلاعات موجودی Wallet"""
        wallet = Wallet.objects.get(id=wallet_id)
        
        return {
            'balance': wallet.balance,
            'investment_balance': wallet.investment_balance,
            'commission_balance': wallet.commission_balance,
            'locked_balance': wallet.locked_balance,
            'total_balance': wallet.total_balance,
            'available_balance': wallet.available_balance,
        }
