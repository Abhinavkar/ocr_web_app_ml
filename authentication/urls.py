from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_user, name='login'),  # Ensure this matches the view function
    path('register/', views.register_user, name='register'),  # Correct the function name
    path('logout/', views.logout_view, name='logout'),  # Ensure this matches the view function
]
