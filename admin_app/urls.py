from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views

app_name = 'admin_app'

urlpatterns = [
    path('register/', views.admin_register, name='admin_register'),
    path('login/', LoginView.as_view(template_name='admin_app/login.html'), name='admin_login'),  # Use built-in LoginView
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('logout/', views.admin_logout, name='admin_logout'),
]
