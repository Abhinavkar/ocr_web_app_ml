from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # The home page route
    path('upload/', views.upload_files, name='upload_files'),
]
