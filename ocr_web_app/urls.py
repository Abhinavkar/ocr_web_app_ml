# from django.contrib import admin
# from django.urls import path, include
# from django.conf import settings
# from django.conf.urls.static import static

# urlpatterns = [
#     path('admin/', admin.site.urls),
#     # path('', include('qa.urls')),
#     path('auth/', include('authentication.urls')),
# ]
# # Add these to the main urls.py

# urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

# Function to redirect to the login page
def redirect_to_login(request):
    return redirect('login')  # Assumes 'login' is defined in authentication.urls

urlpatterns = [
    path('adminapp/', include('admin_app.urls')),
    path('admin/', admin.site.urls),
    path('', redirect_to_login),  # Redirect the root URL to the login page
    path('auth/', include('authentication.urls')),  # Include authentication app URLs
    path('qa/', include('qa.urls')),  # Include QA app URLs
]
