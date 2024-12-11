from rest_framework import serializers
from django.contrib.auth.models import User


# Serializer for Registration
class RegisterUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'password']
        is_admin = True

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            is_admin = validated_data['is_admin']
            
        )
        return user


# Serializer for Login
class LoginUserSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
