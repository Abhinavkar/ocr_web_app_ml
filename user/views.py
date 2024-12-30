from authentication.db_wrapper import get_collection
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from authentication.permissions import IsAdmin, IsSubAdmin
from rest_framework.views import APIView
from rest_framework import status
from bson import ObjectId

class User_Management_Operations(APIView):
    permission_classes = [IsAuthenticated, IsAdmin | IsSubAdmin]
    user_collection = get_collection('auth_users')
    org_collection = get_collection('organization_db')

    def get(self, request):
        users = list(self.user_collection.find())
        for user in users:
            user['_id'] = str(user['_id']) 
        return Response(users, status=status.HTTP_200_OK)

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





