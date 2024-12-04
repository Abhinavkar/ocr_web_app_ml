from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView


urlpatterns = [
    path('login/', views.login_user, name='login'),  # Ensure this matches the view function
    path('register/', views.register_user, name='register'),  # Correct the function name
    path('logout/', LogoutView.as_view(next_page='login'), name='logout')
]
