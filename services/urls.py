from django.urls import path
from .views import * 



urlpatterns = [
    path('add/organization/', Organization_View.as_view() ,name='add-organization'),
    path('get/organization/', Organization_View.as_view() ,name='get-organization'),
    path('delete/organization/<str:id>/', Organization_View.as_view() ,name='delete-organization'),
    path('update/organization/<str:id>/', Organization_View.as_view() ,name='update-organization'),
    path('classes/', ClassListCreateAPI.as_view(), name='class_api'),
    path('classes/<str:id>/', ClassListCreateAPI.as_view(), name='class_api'),
    path('subjects/', SubjectListCreateAPI.as_view(), name='subject_api'),
    # path('subjects/<str:id>/',SubjectListCreateAPI.as_view(), name='subject_api'),
    path('subjects/<str:id>/', SubjectListCreateAPI.as_view(), name='subject-detail'),
    path('subjects/<str:class_id>/<str:section_id>/', SubjectListCreateAPI.as_view(), name='subject-list-class-section'),


    path('sections/', SectionListCreateAPI.as_view(), name='section-list'),
    path('sections/<str:class_id>/', SectionListCreateAPI.as_view(), name='section-class'),




    ]