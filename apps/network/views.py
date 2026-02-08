# apps/network/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from apps.accounts.models import User
from .serializers import UserNetworkSerializer

class NetworkTreeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        # اگر ادمین است می‌تواند یوزرنیم کسی دیگر را ببیند
        target_username = request.query_params.get('username')
        if target_username and request.user.is_staff:
            try:
                user = User.objects.get(username=target_username)
            except User.DoesNotExist:
                return Response({"error": "User not found"}, status=404)

        serializer = UserNetworkSerializer(user)
        return Response(serializer.data)
