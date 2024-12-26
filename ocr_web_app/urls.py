
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect


from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from django.views.generic import TemplateView

schema_view = get_schema_view(
    openapi.Info(
        title="HRMS BACKEND ",
        default_version='v1',
        description="QA API CONFIGURATION  ",
        contact=openapi.Contact(email="abhinav.kar@vvdntech.in"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)



urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/qa/', include('qa.urls')),
    path('api/auth/', include('authentication.urls')),
    path('api/services/',include('services.urls')),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui')
]
