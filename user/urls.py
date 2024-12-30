from django.urls import path
from .views import User_Management_Operations

urlpatterns = [
    path('users/', User_Management_Operations.as_view(), name='user-list'),
    path('users/<str:id>/', User_Management_Operations.as_view(), name='user-detail'),
]