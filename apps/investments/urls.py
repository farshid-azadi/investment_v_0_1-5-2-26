from django.urls import path
from .views import InvestView, InvestmentHistoryView

urlpatterns = [
    path('buy/', InvestView.as_view(), name='invest-buy'),
    path('history/', InvestmentHistoryView.as_view(), name='invest-history'),
]
