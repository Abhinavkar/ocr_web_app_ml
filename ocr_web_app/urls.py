
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

# Function to redirect to the login page
def redirect_to_login(request):
    return redirect('login')  # Assumes 'login' is defined in authentication.urls

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', redirect_to_login),  # Redirect the root URL to the login page
    path('auth/', include('authentication.urls')),  # Include authentication app URLs
    path('qa/', include('qa.urls')),  # Include QA app URLs
]
