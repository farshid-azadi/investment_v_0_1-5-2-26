from django.urls import path
from .views import WalletInfoView, DepositView, TransactionHistoryView, WithdrawalView

urlpatterns = [
    path('info/', WalletInfoView.as_view(), name='wallet-info'),
    path('deposit/', DepositView.as_view(), name='wallet-deposit'),
    path('history/', TransactionHistoryView.as_view(), name='wallet-history'),
    path('withdraw/', WithdrawalView.as_view(), name='wallet-withdraw'),

]
