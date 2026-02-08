# apps/investments/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db import transaction
from django.shortcuts import get_object_or_404

from .models import InvestmentPlan, UserInvestment
from .serializers import InvestmentSerializer, InvestmentHistorySerializer
from apps.wallet.models import Transaction, Wallet

# --- تغییر نام تابع در اینجا انجام شده است ---
from apps.network.services import distribute_direct_reward, update_binary_volumes

class InvestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = InvestmentSerializer(data=request.data)
        if serializer.is_valid():
            amount = serializer.validated_data['amount']
            # اگر نام پلن در ریکوئست نیست، پیش‌فرض را می‌گیریم یا از دیتای سریالایزر
            plan_name = serializer.validated_data.get('plan_type', 'Standard') 
            
            user = request.user
            wallet = user.wallet

            # 1. پیدا کردن یا اعتبارسنجی پلن
            # فرض می‌کنیم پلن‌ها در دیتابیس تعریف شده‌اند، اگر نه از مقادیر پیش‌فرض استفاده می‌کنیم
            try:
                # اینجا می‌توانید منطق انتخاب پلن بر اساس مبلغ را هم بگذارید
                # فعلا ساده‌ترین حالت:
                plan = InvestmentPlan.objects.filter(min_amount__lte=amount, max_amount__gte=amount, is_active=True).first()
                if not plan:
                    # اگر پلنی پیدا نشد، یک پلن پیش‌فرض یا اولین پلن را برداریم (بسته به بیزنس لاجیک)
                    plan = InvestmentPlan.objects.filter(is_active=True).first()
            except:
                plan = None

            if not plan:
                 return Response({"error": "No suitable investment plan found for this amount."}, status=400)

            # 2. بررسی موجودی
            if wallet.balance < amount:
                return Response({"error": "Insufficient balance"}, status=400)

            try:
                with transaction.atomic():
                    # کسر از کیف پول (موجودی نقد)
                    # نکته: در مدل Wallet شما فقط balance دارید که موجودی قابل برداشت است.
                    # برای خرید باید از همین موجودی کسر شود.
                    wallet = Wallet.objects.select_for_update().get(user=user)
                    if wallet.balance < amount:
                        raise ValueError("Insufficient balance")
                    
                    wallet.balance -= amount
                    wallet.save()

                    # ثبت تراکنش برداشت برای خرید
                    Transaction.objects.create(
                        wallet=wallet,
                        amount=amount,
                        transaction_type='investment',
                        status='confirmed',
                        description=f"Purchase Plan: {plan.name}"
                    )

                    # ایجاد رکورد سرمایه‌گذاری
                    investment = UserInvestment.objects.create(
                        user=user,
                        plan_type=plan.name, # ذخیره نام پلن
                        amount=amount,
                        daily_interest_rate=plan.daily_interest_rate,
                        duration_days=plan.duration_days
                    )

                    # --- توزیع پاداش‌ها (منطق جدید) ---
                    # 1. پاداش معرف مستقیم (50/50)
                    distribute_direct_reward(user, amount)
                    
                    # 2. آپدیت حجم باینری (محاسبه سود باینری در تسک شبانه انجام می‌شود)
                    update_binary_volumes(user, amount)

                return Response(
                    {"message": "Investment successful", "investment_id": investment.id},
                    status=status.HTTP_201_CREATED
                )

            except ValueError as e:
                return Response({"error": str(e)}, status=400)
            except Exception as e:
                return Response({"error": f"System error: {str(e)}"}, status=500)

        return Response(serializer.errors, status=400)


class InvestmentHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        investments = UserInvestment.objects.filter(user=request.user).order_by('-created_at')
        serializer = InvestmentHistorySerializer(investments, many=True)
        return Response(serializer.data)
