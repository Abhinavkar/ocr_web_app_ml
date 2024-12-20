from django.contrib.auth import authenticate, login, logout
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.decorators import permission_classes
from django.contrib.auth.hashers import check_password, make_password
from .db_wrapper import get_collection
from .models import User

class RegisterAdminUserView(APIView):
    def post(self, request):
        data = request.data
        users_collection = get_collection("auth_users")  # MongoDB collection for users

        # Check if the username already exists
        if users_collection.find_one({"username": data["username"]}):
            return Response({"error": "Admin already exists"}, status=400)

        # Hash the password
        hashed_password = make_password(data["password"])

        # Create the admin user document
        admin_user = {
            "username": data["username"],
            "password": hashed_password,
            "is_admin": True,
            "is_superuser": True,
            "is_staff": True,
        }

        # Insert the admin user into MongoDB
        users_collection.insert_one(admin_user)

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
        users_collection = get_collection("auth_users")
        print(users_collection)
        user = users_collection.find_one({"username": data["username"]})
        print(user)

        if user and check_password(data["password"], user["password"]):

                return Response({
                    "message": "Admin login successful",
                    "is_admin": user["is_admin"]
                    }, status=200)
        else:
            return Response({"message": "Invalid credentials"}, status=400)



class LogoutUserView(APIView):
    def post(self, request):
        logout(request)
        return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)
