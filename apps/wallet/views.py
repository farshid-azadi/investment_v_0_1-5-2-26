# apps/wallet/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db import transaction
from decimal import Decimal

# ایمپورت مدل‌ها (WithdrawalRequest اضافه شد)
from .models import Transaction, WithdrawalRequest, Wallet
# ایمپورت سریالایزرها (WithdrawalSerializer اضافه شد)
from .serializers import WalletSerializer, TransactionSerializer, DepositSerializer, WithdrawalSerializer

class WalletInfoView(APIView):
    """نمایش موجودی کیف پول کاربر جاری"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # چون رابطه OneToOne است، از request.user.wallet استفاده می‌کنیم
        wallet = request.user.wallet
        serializer = WalletSerializer(wallet)
        return Response(serializer.data)

class DepositView(APIView):
    """ثبت درخواست واریز (شارژ حساب)"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DepositSerializer(data=request.data)
        if serializer.is_valid():
            # ایجاد تراکنش با وضعیت پیش‌فرض pending
            Transaction.objects.create(
                wallet=request.user.wallet,
                amount=serializer.validated_data['amount'],
                transaction_type='deposit',
                status='pending',
                description=serializer.validated_data.get('description', '')
            )
            return Response({"message": "درخواست واریز ثبت شد و در انتظار تایید است."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TransactionHistoryView(APIView):
    """لیست تراکنش‌های کاربر"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        transactions = Transaction.objects.filter(wallet=request.user.wallet).order_by('-created_at')
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data)

class WithdrawalView(APIView):
    """ثبت درخواست برداشت وجه"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = WithdrawalSerializer(data=request.data)
        
        if serializer.is_valid():
            amount = serializer.validated_data['amount']
            wallet_address = serializer.validated_data['wallet_address']

            try:
                with transaction.atomic():
                    # 1. قفل کردن کیف پول برای جلوگیری از ریس کاندیشن
                    wallet = Wallet.objects.select_for_update().get(user=request.user)
                    
                    # 2. بررسی موجودی
                    if wallet.balance < amount:
                        return Response({"error": "موجودی کیف پول برای برداشت کافی نیست."}, status=status.HTTP_400_BAD_REQUEST)

                    # 3. کسر آنی موجودی (فریز کردن پول)
                    # چون وضعیت تراکنش pending است، سیگنال به طور خودکار کسر نمی‌کند (چون سیگنال روی confirmed تنظیم شده)
                    # بنابراین اینجا دستی کم می‌کنیم تا پول بلوکه شود.
                    wallet.balance -= amount
                    wallet.save()

                    # 4. ایجاد رکورد درخواست برداشت
                    request_obj = WithdrawalRequest.objects.create(
                        user=request.user,
                        amount=amount,
                        wallet_address=wallet_address
                    )

                    # 5. ثبت تراکنش در تاریخچه (با وضعیت pending)
                    Transaction.objects.create(
                        wallet=wallet,
                        amount=amount,
                        transaction_type='withdrawal',
                        status='pending',
                        description=f'Withdrawal Request ID: {request_obj.id} to {wallet_address}'
                    )

                return Response(
                    {"message": "درخواست برداشت با موفقیت ثبت شد.", "data": serializer.data}, 
                    status=status.HTTP_201_CREATED
                )

            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
