from django.urls import path
from .views import (
    RegisterAdminUserView,
    RegisterNormalUserView,
    LoginUserView,
    LogoutUserView,
)

urlpatterns = [
    path('admin/register/', RegisterAdminUserView.as_view(), name='register_admin'),
    path('user/register/', RegisterNormalUserView.as_view(), name='register_user'),
    path('login/', LoginUserView.as_view(), name='login'),
    path('logout/', LogoutUserView.as_view(), name='logout'),
]
