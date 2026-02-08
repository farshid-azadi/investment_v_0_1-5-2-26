from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'mobile', 'first_name', 'last_name', 'referral_code', 'date_joined')
        read_only_fields = ('id', 'referral_code', 'date_joined')

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    referral_code = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ('username', 'mobile', 'password', 'referral_code')

    def create(self, validated_data):
        referral_code = validated_data.pop('referral_code', None)
        password = validated_data.pop('password')
        
        referrer = None
        if referral_code:
            try:
                referrer = User.objects.get(referral_code=referral_code)
            except User.DoesNotExist:
                raise ValidationError({"referral_code": "Invalid referral code."})

        user = User(**validated_data)
        user.set_password(password) # هش کردن پسورد
        if referrer:
            user.referrer = referrer
        user.save()
        return user
