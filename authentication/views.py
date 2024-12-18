from django.contrib.auth import authenticate, login, logout
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from django.contrib.auth.hashers import check_password, make_password
from .models import User

class RegisterAdminUserView(APIView):
    def post(self, request):
        data = request.data
        if User.objects.filter(username=data["username"]).exists():
            return Response({"error": "Admin already exists"}, status=400)
        hashed_password = make_password(data["password"])
        user = User.objects.create(
            username=data["username"],
            password=hashed_password,
            is_admin=True,
            is_superuser=True,
            is_staff=True
        )
        user.save()
        return Response({"message": "Admin registered successfully"}, status=201)


class RegisterNormalUserView(APIView):
    def post(self, request):
        data = request.data
        if User.objects.filter(username=data["username"]).exists():
            return Response({"error": "User already exists"}, status=400)
        hashed_password = make_password(data["password"])
        user = User.objects.create(
            username=data["username"],
            password=hashed_password,
            is_admin=False,
            is_superuser=False,
            is_staff=False
        )
        user.save()
        return Response({"message": "User registered successfully"}, status=201)


class LoginUserView(APIView):
    def post(self, request):
        data = request.data
        user = authenticate(username=data["username"], password=data["password"])
        if user is not None:
            login(request, user)
            refresh = RefreshToken.for_user(user)
            return Response({
                "message": "Login successful",
                "is_admin": user.is_admin,
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            }, status=200)
        else:
            return Response({"message": "Invalid credentials"}, status=400)


@permission_classes([IsAuthenticated])
class LogoutUserView(APIView):
    def post(self, request):
        logout(request)
        return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)
