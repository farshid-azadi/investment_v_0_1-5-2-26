# apps/lottery/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import status
from .services import LotteryService
from .serializers import LotteryRoundSerializer, LotteryTicketSerializer, LotteryWinnerSerializer
from .models import LotteryTicket, LotteryWinner

class CurrentLotteryView(APIView):
    """
    نمایش وضعیت دور فعلی لاتاری
    """
    def get(self, request):
        round_obj = LotteryService.get_current_round()
        serializer = LotteryRoundSerializer(round_obj)
        return Response(serializer.data)

class BuyTicketView(APIView):
    """
    خرید بلیط لاتاری
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            ticket = LotteryService.buy_ticket(request.user)
            return Response({
                "message": "Ticket purchased successfully",
                "ticket_id": ticket.id
            }, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class MyTicketsView(APIView):
    """
    مشاهده بلیط‌های من
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tickets = LotteryTicket.objects.filter(user=request.user).order_by('-purchased_at')
        serializer = LotteryTicketSerializer(tickets, many=True)
        return Response(serializer.data)

class RunLotteryView(APIView):
    """
    اجرای دستی لاتاری (فقط ادمین)
    """
    permission_classes = [IsAdminUser]

    def post(self, request):
        round_id = request.data.get('round_id')
        try:
            winner = LotteryService.run_lottery_draw(round_id)
            if winner:
                return Response({"message": f"Winner is {winner.username}"})
            else:
                return Response({"message": "No participants, rolled over."})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
