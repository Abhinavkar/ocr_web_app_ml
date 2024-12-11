
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

# Function to redirect to the login page
def redirect_to_login(request):
    return redirect('login')  # Assumes 'login' is defined in authentication.urls

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/qa/', include('qa.urls')),
    path('api/auth/', include('authentication.urls')),

]
