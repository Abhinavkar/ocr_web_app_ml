from django.contrib.auth import authenticate, login, logout
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.decorators import permission_classes
from django.contrib.auth.hashers import check_password, make_password
from .db_wrapper import get_collection
from .models import User
from .utils import send_hr_email

class RegisterAdminUserView(APIView):
    def post(self, request):
        data = request.data
        users_collection = get_collection("auth_users")  # MongoDB collection for users

        # Check if the username already exists
        if users_collection.find_one({"username": data["username"]}):
            return Response({"error": "Admin already exists"}, status=400)

        # Hash the password
        hashed_password = make_password(data["password"])
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




class Register_Org_Admin_User_View(APIView):
    def post(self, request):
        data = request.data
        username = data.get('username')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        email = data.get('email')
        password = data.get('password')
        section_assigned = data.get('section_assigned')
        department = data.get('department')

        # Validate required fields
        if not all([username, first_name, last_name, email, password, section_assigned, department]):
            return Response({"message": "Please provide all the details"}, status=status.HTTP_400_BAD_REQUEST)

        # Validate email format
        if '@' not in email or '.' not in email.split('@')[-1]:
            return Response({"message": "Invalid email format"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            users_collection = get_collection("auth_users")
            if users_collection.find_one({"username": username}):
                return Response({"error": f"User with username {username} already exists"}, status=400)

            hashed_password = make_password(password)
            organization ="Dav Public School"
            admin_user = {
                "username": username,
                "password": hashed_password,
                "first_name": first_name,
                'last_name': last_name,
                "email": email,
                "is_admin": True,
                "is_super_staff": False,
                "is_sub_admin": True,
                'is_user': True,
                "department": department,
                "section_assigned": section_assigned,
            }
            users_collection.insert_one(admin_user)

            try:
                subject = "Welcome to the QA Portal"
                recipient_list = [email]
                message = (f"You have been registered as an admin user for organization {organization}. You now have access to the Qa portal.\n"
                           f"Your User ID is: {username}\n"
                           "1. You are a Admin Now for your whole organization\n"
                           "2. Please log in with your credentials, and change your password.\n the default password is 123123\n")
                send_hr_email(subject, message, recipient_list)
            except Exception as e:
                print(f"Error sending email: {e}")

            return Response({"message": "Successfully Created User"}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'message': "Error Occurred while fetching userdb"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
class Register_Org_Sub_Admin_User_View(APIView):
     def post(self,request):
        data=request.data
        username=request.data.get('username')
        first_name=request.data.get('first_name')
        last_name=request.data.get('last_name')
        is_admin=False
        is_sub_admin=True
        is_user=False
        is_superstaff=False
        section_assigned=request.data.get('section_assigned')
        department=request.data.get('department')
        if username is None or first_name is None or last_name is None or department is None or section_assigned is None:
            return Response({"message":"Please provide all the details"},status=status.HTTP_400_BAD_REQUEST)
        try : 
            users_collection = get_collection("auth_users")  
            if users_collection.find_one({"username": data["username"]}):
                return Response({"error": f"user with this {username} already exists"}, status=400)
            hashed_password = make_password(data["password"])
            admin_user = {
            "username": username,
            "password": hashed_password,
            "first_name":first_name,
            'last_name':last_name,
            "is_admin": is_admin,
            "is_super_staff": is_superstaff,
            "is_sub_admin": is_sub_admin,
            'is_user':is_user,
            "department":department,
            "section_assigned":section_assigned,
          }
            user_data=users_collection.insert_one(admin_user)

            return Response({"message":"Successfully Created User "},status=status.HTTP_201_CREATED)

        except Exception as e : 
            return Response({'message':"Error Occured while fetching userdb "},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        