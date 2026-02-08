# apps/investments/serializers.py

from rest_framework import serializers
from .models import UserInvestment, InvestmentPlan

class InvestmentSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=20, decimal_places=2)
    # فیلد plan_type اختیاری است، اگر کاربر نفرستاد سیستم خودش پیدا می‌کند
    plan_type = serializers.CharField(max_length=50, required=False)

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be positive.")
        # چک کردن حداقل مبلغ کلی (اختیاری)
        if value < 10: 
            raise serializers.ValidationError("Minimum investment is 10 USDT.")
        return value

class InvestmentHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserInvestment
        fields = [
            'id', 
            'plan_type', 
            'amount', 
            'reinvested_amount',  # نمایش مبلغ اضافه شده از سودها
            'active_capital',     # نمایش جمع کل سرمایه فعال
            'daily_interest_rate', 
            'total_profit_earned', 
            'status', 
            'created_at', 
            'end_date'
        ]
