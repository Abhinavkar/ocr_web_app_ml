from authentication.db_wrapper import get_collection
from rest_framework.response import Response
class User_role_check():
    user_collection = get_collection('auth_user')
    def Admin_Role_Check(userid):
        
