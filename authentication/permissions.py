from rest_framework.permissions import BasePermission
from .db_wrapper import get_collection
from bson import ObjectId

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        user_id = request.headers.get('userId')
        if not user_id:
            return False
        users_collection = get_collection('auth_users')
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        print(user)

        return user and user.get('is_admin', False)

class IsSuperStaff(BasePermission):
    def has_permission(self, request, view):
        user_id = request.headers.get('userId')
        if not user_id:
            return False
        users_collection = get_collection('auth_users')
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        return user and user.get('is_super_staff', False)

class IsSubAdmin(BasePermission):
    def has_permission(self, request, view):
        user_id = request.headers.get('userId')
        if not user_id:
            return False
        users_collection = get_collection('auth_users')
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        return user and user.get('is_sub_admin', False)

class IsUser(BasePermission):
    def has_permission(self, request, view):
        user_id = request.headers.get('userId')
        if not user_id:
            return False
        users_collection = get_collection('auth_users')
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        return user and user.get('is_user', True)
