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
    def post(self,request):
        data=request.data
        username=request.data.get('username')
        first_name=request.data.get('first_name')
        last_name=request.data.get('last_name')
        is_admin=True
        is_sub_admin=True
        is_user=True
        is_superstaff=False
        section_assigned=request.data.get('section_assigned')
        department=request.data.get('department')
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
            users_collection.insert_one(admin_user)
            try :
                 subject = "Welcome to the HRMS Portal"
                 username = serializer.validated_data.get('username', 'Your username')
                 recipient_list = [serializer.validated_data['email']]
                 message = (f"You have been registered as an HR user. You now have access to the portal.\n"
                        f"Your User ID is: {username}\n"
                        "Please log in with your credentials.")

                 send_hr_email(subject, message, recipient_list)
            except Exception as e:
                print(f"Error sending email: {e}")
            
            return Response({"message":"Successfully Created User "},status=status.HTTP_201_CREATED)
        

        except Exception as e : 
            return Response({'message':"Error Occured while fetching userdb "},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
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
        