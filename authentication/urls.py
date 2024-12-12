from django.urls import path
from .views import (
    RegisterAdminUserView,
    RegisterNormalUserView,
    LoginUserView,
    LogoutUserView,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
    path('admin/register/', RegisterAdminUserView.as_view(), name='register_admin'),
    path('user/register/', RegisterNormalUserView.as_view(), name='register_user'),
    path('login/', LoginUserView.as_view(), name='login'),
    path('logout/', LogoutUserView.as_view(), name='logout'),
    
    
    #JWT 
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]

