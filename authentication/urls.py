from django.urls import path
from .views import (
    RegisterAdminUserView,
    RegisterNormalUserView,
    Register_Org_Admin_User_View,
    LoginUserView,
    Register_Org_Sub_Admin_User_View,
    LogoutUserView,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
    path('admin/register/', RegisterAdminUserView.as_view(), name='register_admin'),
    path('org/register/admin/',Register_Org_Admin_User_View.as_view(),name='register_school'), # Registering the school admin Principal
    path('org/register/subadmin/',Register_Org_Sub_Admin_User_View.as_view(),name='register_subadmin'), # Registering the  HOD or subadmin
    path('user/register/', RegisterNormalUserView.as_view(), name='register_user'), # Registering the normal user or Teacher
    path('login/', LoginUserView.as_view(), name='login'),
    path('logout/', LogoutUserView.as_view(), name='logout'),
]

