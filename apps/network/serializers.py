# apps/network/serializers.py
from rest_framework import serializers
from apps.accounts.models import User

class UserNetworkSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    stats = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'binary_position', 'left_volume', 'right_volume', 'stats', 'children']

    def get_stats(self, obj):
        # محاسبه سودهای دریافتی زیرمجموعه (که در سوال خواستید)
        return {
            'total_invested': sum(inv.amount for inv in obj.userinvestment_set.filter(status='active')),
            'total_commission_earned': obj.total_commission_earned,
            # می‌توانید جزئیات سود روزانه را هم اینجا جمع بزنید
        }

    def get_children(self, obj):
        # دریافت فرزندان مستقیم باینری (چپ و راست)
        children = obj.binary_children.all()
        return UserNetworkSerializer(children, many=True).data
