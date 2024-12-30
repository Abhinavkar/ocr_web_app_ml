from authentication.db_wrapper import get_collection
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from authentication.permissions import IsAdmin, IsSubAdmin, IsSuperStaff
from rest_framework.views import APIView
from rest_framework import status
from bson import ObjectId
import json
from django.http import JsonResponse

class User_Management_Operations(APIView):
    

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsSuperStaff()]  
        elif self.request.method == 'DELETE':
            return [IsAuthenticated(), IsSuperStaff()]  
        elif self.request.method == 'PUT':
            return [IsAuthenticated(), IsSuperStaff()] 
        return super().get_permissions()
    
    user_collection = get_collection('auth_users')
    org_collection = get_collection('organization_db')

    # def get(self, request):
    #     users = list(self.user_collection.find())
    #     for user in users:
    #         user['_id'] = str(user['_id']) 
    #     return Response(users, status=status.HTTP_200_OK)
    
    def get(self, request):
        user_header = request.headers.get('user')  # Get the user header
        if not user_header:
            return Response({"error": "User data is required in the headers"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Parse the 'user' header as JSON
            user_header = json.loads(user_header)
            org_id = user_header.get('organization_id')  # Get the organization_id from the header
        except json.JSONDecodeError:
            return Response({"error": "Invalid user header format"}, status=status.HTTP_400_BAD_REQUEST)
        
        if not org_id:
            return Response({"error": "User does not belong to any organization"}, status=status.HTTP_400_BAD_REQUEST)
      
        users_in_org = list(self.user_collection.find({"organization": org_id}))
  
        if not users_in_org:
            return Response({"error": "No users found in the specified organization"}, status=status.HTTP_404_NOT_FOUND)
        for user in users_in_org:
            user['_id'] = str(user['_id'])  
        return Response(users_in_org, status=status.HTTP_200_OK)
    
    
    
    def put(self, request, id):
        if not request.user or not request.user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        
        if not (request.user.is_admin or request.user.is_sub_admin):
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        data = request.data
        update_fields = {}
        if 'is_admin' in data:
            update_fields['is_admin'] = data['is_admin']
        if 'is_sub_admin' in data:
            update_fields['is_sub_admin'] = data['is_sub_admin']
        
        result = self.user_collection.update_one({"_id": ObjectId(id)}, {"$set": update_fields})
        if result.matched_count == 0:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        
        return Response({"message": "User updated successfully"}, status=status.HTTP_200_OK)

    def delete(self, request, id):
        if not request.user or not request.user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        
        if not (request.user.is_admin or not request.user.is_sub_admin):
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        result = self.user_collection.delete_one({"_id": ObjectId(id)})
        if result.deleted_count == 0:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        
        return Response({"message": "User deleted successfully"}, status=status.HTTP_200_OK)





