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
            # Set is_admin to True (admin user)
            is_admin = True

            # Create the admin user
            user = User.objects.create_user(
                username=username,
                password=password,
                is_admin = True
            )
            user.is_staff = is_admin  # Set the user as an admin
            user.save()

            return Response({"message": "Admin user registered successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

################################################################################################################################3
class RegisterNormalUserView(APIView):
    def post(self, request):
        serializer = RegisterUserSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            # Set is_admin to False (normal user)
            is_admin = False

            # Create the normal user
            user = User.objects.create_user(
                username=username,
                password=password,
                is_admin = False
            )
            user.is_staff = is_admin  # Ensure the user is not an admin
            user.save()

            return Response({"message": "Normal user registered successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
##################################################################################################################################


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
        logout(request)  # This will log out the user
        return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)
