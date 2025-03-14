from django.urls import path
from .views import (
    Register_Org_User_View,
    Register_Org_Admin_User_View,
    LoginUserView,
    Register_Org_Sub_Admin_User_View,
   
)

urlpatterns = [
    path('org/register/admin/',Register_Org_Admin_User_View.as_view(),name='register_school'), # Registering the school admin Principal
    path('org/register/subadmin/',Register_Org_Sub_Admin_User_View.as_view(),name='register_subadmin'), # Registering the  HOD or subadmin
    path('org/register/user/', Register_Org_User_View.as_view(), name='register_user'), # Registering the normal user or Teacher
    path('login/', LoginUserView.as_view(), name='login'),
]

