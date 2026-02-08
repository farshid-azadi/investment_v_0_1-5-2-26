# apps/wallet/serializers.py

from rest_framework import serializers
from .models import Wallet, Transaction, WithdrawalRequest  # WithdrawalRequest اضافه شد

class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ['balance', 'updated_at']

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'amount', 'transaction_type', 'status', 'description', 'created_at']
        read_only_fields = ['status', 'created_at'] # کاربر نمی‌تواند وضعیت را خودش تغییر دهد

class DepositSerializer(serializers.ModelSerializer):
    """سریالایزر مخصوص درخواست واریز"""
    class Meta:
        model = Transaction
        fields = ['amount', 'description'] # مثلا در توضیحات هش تراکنش را بفرستد
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("مبلغ واریز باید بیشتر از صفر باشد.")
        return value

class WithdrawalSerializer(serializers.ModelSerializer):
    """سریالایزر مخصوص درخواست برداشت"""
    class Meta:
        model = WithdrawalRequest
        fields = ['amount', 'wallet_address', 'network', 'status', 'created_at']
        read_only_fields = ['status', 'created_at', 'network']

    def validate_amount(self, value):
        if value < 10:
            raise serializers.ValidationError("حداقل مقدار برداشت ۱۰ تتر است.")
        return value
