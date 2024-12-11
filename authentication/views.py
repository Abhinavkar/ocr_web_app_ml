from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from .serializers import RegisterUserSerializer, LoginUserSerializer

class RegisterAdminUserView(APIView):
    def post(self, request):
        serializer = RegisterUserSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']

            # Create the admin user
            user = User.objects.create_user(
                username=username,
                password=password,
            )
            user.is_staff = True  # Set the user as an admin
            user.is_superuser = True  # Optionally make them a superuser
            user.save()

            return Response({"message": "Admin user registered successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RegisterNormalUserView(APIView):
    def post(self, request):
        serializer = RegisterUserSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']

            # Create the normal user
            user = User.objects.create_user(
                username=username,
                password=password,
            )
            user.is_staff = False  # Ensure the user is not an admin
            user.save()

            return Response({"message": "Normal user registered successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginUserView(APIView):
    def post(self, request):
        serializer = LoginUserSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                is_admin = user.is_staff 
                return Response(
                    {"message": "Login successful", "is_admin": is_admin}, 
                    status=status.HTTP_200_OK
                )
            return Response({"message": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutUserView(APIView):
    def post(self, request):
        logout(request)
        return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)
