from django.contrib.auth import authenticate, login, logout
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.decorators import permission_classes
from django.contrib.auth.hashers import check_password, make_password
from .db_wrapper import get_collection
from .models import User
from .utils import send_hr_email
from bson import ObjectId


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
        organization = data.get('organization')
        
        if not all([username, first_name, last_name, email, password, section_assigned, department, organization]):
            return Response({"message": "Please provide all the details"}, status=status.HTTP_400_BAD_REQUEST)

        if '@' not in email or '.' not in email.split('@')[-1]:
            return Response({"message": "Invalid email format"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            users_collection = get_collection("auth_users")
            if users_collection.find_one({"username": username}):
                return Response({"error": f"User with username {username} already exists"}, status=400)

            hashed_password = make_password(password)
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
                "organization":organization
            }
           
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
                return Response({'message':"Email Server Error "},status=status.HTTP_503_SERVICE_UNAVAILABLE)
            users_collection.insert_one(admin_user)

            return Response({"message": "Successfully Created User"}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'message': "Error Occurred while fetching userdb"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class Register_Org_Sub_Admin_User_View(APIView):
     
     def post(self,request):
        data=request.data
        organization = request.data.get('organization')
        username=request.data.get('username')
        first_name=request.data.get('first_name')
        last_name=request.data.get('last_name')
        email = request.data.get('email')
        is_admin=False
        is_sub_admin=True
        is_user=True
        is_superstaff=False
        section_assigned=request.data.get('section_assigned')
        department=request.data.get('department')
        if username is None or first_name is None or last_name is None or department is None or section_assigned is None or organization is None :
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
           
            try:
                subject = "Welcome to the QA Portal"
                recipient_list = [email]
                message = (f" Welcome to the QA Portal You have been registered as an subadmin by an adminuser of your organization {organization}. You now have access to the Qa portal.\n"
                           f"Your User ID is: {username}\n"
                           f"1. Please log in with your credentials, and change your password.\n the default password is 123123\n"
                           f"2. You are a Sub Admin Now for your whole organization\n"
                           )
                
                send_hr_email(subject, message, recipient_list)
            except Exception as e:
                print(f"Error sending email: {e}")
                return Response({'message':"Email Server Error in SubAdmin registeration "},status=status.HTTP_503_SERVICE_UNAVAILABLE)
            user_data=users_collection.insert_one(admin_user)
            return Response({"message":"Successfully Created User "},status=status.HTTP_201_CREATED)

        except Exception as e : 
            return Response({'message':"Error Occured while fetching userdb "},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class Register_Org_User_View(APIView):
       def post(self,request):
        data=request.data
        organization = request.data.get('organization')
        username=request.data.get('username')
        first_name=request.data.get('first_name')
        last_name=request.data.get('last_name')
        email = request.data.get('email')
        section_assigned=request.data.get('section_assigned')
        department=request.data.get('department')
        is_admin=False
        is_sub_admin=False
        is_user=True
        is_superstaff=False
    
        if username is None or first_name is None or last_name is None or department is None or section_assigned is None or organization is None:
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
            "organization":organization
          }
           
            try:
                subject = "Welcome to the QA Portal"
                recipient_list = [email]
                message = (f" Welcome to the QA Portal You have been registered as an User by an adminuser or Subadmin of your organization {organization}. You now have access to the Qa portal.\n"
                           f"Your User ID is: {username}\n"
                           f"1. Please log in with your credentials, and change your password.\n the default password is 123123\n"
                           f"2. You are a Sub Admin Now for your whole organization\n"
                           )
                
                send_hr_email(subject, message, recipient_list)
            except Exception as e:
                print(f"Error sending email: {e}")
                return Response({'message':"Email Server Error in SubAdmin registeration "},status=status.HTTP_503_SERVICE_UNAVAILABLE)
            user_data=users_collection.insert_one(admin_user)
            return Response({"message":"Successfully Created User "},status=status.HTTP_201_CREATED)

        except Exception as e : 
            return Response({'message':"Error Occured while fetching userdb "},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class LoginUserView(APIView):
    def post(self, request):
        data = request.data
        users_collection = get_collection("auth_users")
        organizations_collection = get_collection("organization_db")
        user = users_collection.find_one({"username": data["username"]})

        if user and check_password(data["password"], user["password"]):
            user['_id'] = str(user['_id'])
            
            org_id = user['organization']
            print(organizations_collection)
            organization = organizations_collection.find_one({"_id": ObjectId(org_id)})
            print(organization)
            organization_name = organization["organization_name"] if organization else "Unknown"

            return Response({
                "message": "Admin login successful",
                "is_admin": user["is_admin"],
                "is_super_staff": user["is_super_staff"],
                "is_sub_admin": user["is_sub_admin"],
                "is_user": user["is_user"],
                "first_name": user["first_name"],
                "last_name": user["last_name"],
                "email": user["email"],
                "department": user["department"],
                "section_assigned": user["section_assigned"],
                "organization": organization_name,
                "organization_id":org_id
            }, status=200)
        else:
            return Response({"message": "Invalid credentials"}, status=400)