# apps/lottery/urls.py

from django.urls import path
from .views import CurrentLotteryView, BuyTicketView, MyTicketsView, RunLotteryView

urlpatterns = [
    path('current/', CurrentLotteryView.as_view(), name='lottery-current'),
    path('buy/', BuyTicketView.as_view(), name='lottery-buy'),
    path('my-tickets/', MyTicketsView.as_view(), name='lottery-my-tickets'),
    path('run/', RunLotteryView.as_view(), name='lottery-run'), # Admin only
]
