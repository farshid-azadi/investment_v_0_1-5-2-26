# apps/lottery/serializers.py

from rest_framework import serializers
from .models import LotteryRound, LotteryTicket, LotteryWinner

class LotteryRoundSerializer(serializers.ModelSerializer):
    class Meta:
        model = LotteryRound
        fields = ['id', 'round_number', 'start_date', 'total_pot', 'participants_count', 'is_active']

class LotteryTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = LotteryTicket
        fields = ['id', 'purchased_at', 'ticket_price', 'is_winner']

class LotteryWinnerSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = LotteryWinner
        fields = ['username', 'prize_amount', 'won_at']
