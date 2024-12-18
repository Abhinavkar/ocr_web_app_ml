from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from .serializers import RegisterUserSerializer, LoginUserSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from authentication.db_wrapper import get_collection
from django.contrib.auth.hashers import check_password, make_password

class RegisterAdminUserView(APIView):
    def post(self, request):
        data = request.data
        users_collection = get_collection("auth_users")

        # Check if user already exists
        if users_collection.find_one({"username": data["username"]}):
            return Response({"error": "Admin already exists"}, status=400)

        # Hash the password
        hashed_password = make_password(data["password"])

        # Insert new admin user with hashed password
        users_collection.insert_one({
            "username": data["username"],
            "password": hashed_password,  
            "is_admin": True,
            "is_superstaff": True,
        })
        return Response({"message": "Admin registered successfully"}, status=201)


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

            return Response({"message": "User registered successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class LoginUserView(APIView):
    def post(self, request):
        data = request.data
        users_collection = get_collection("auth_users")
        print(users_collection)

        # Find user in MongoDB
        user = users_collection.find_one({"username": data["username"]})
        print(user)

        if user and check_password(data["password"], user["password"]):  # Compare hashed passwords
            # Check admin privileges
            if user.get("is_admin") and user.get("is_superstaff"):
                # Generate JWT tokens
                refresh = RefreshToken()
                access_token = refresh.access_token

                return Response({
                    "message": "Admin login successful",
                    "is_admin": True,
                    "refresh": str(refresh),
                    "access": str(access_token),
                }, status=200)
            else:
                return Response({"message": "Access denied: Not an admin user"}, status=403)

        return Response({"message": "Invalid credentials"}, status=400)




@permission_classes([IsAuthenticated])
class LogoutUserView(APIView):
    def post(self, request):
        logout(request)
        return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)
