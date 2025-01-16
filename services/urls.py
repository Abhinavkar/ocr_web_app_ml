from django.urls import path
from .views import * 



urlpatterns = [
    path('add/organization/', Organization_View.as_view() ,name='add-organization'),
    path('get/organization/', Organization_View.as_view() ,name='get-organization'),
    path('delete/organization/<str:id>/', Organization_View.as_view() ,name='delete-organization'),
    path('update/organization/<str:id>/', Organization_View.as_view() ,name='update-organization'),
    
    
    path('classes/', ClassListCreateAPI.as_view(), name='class_api'),
    path('classes/<str:id>/', ClassListCreateAPI.as_view(), name='class_api'),
    path('classes/delete/<str:id>/', ClassListCreateAPI.as_view(), name='delete_class'),
    path('classes/update/<str:id>/',ClassListCreateAPI.as_view(), name='update_class'),
    
    
    
    path('subjects/', SubjectListCreateAPI.as_view(), name='subject_api'),
    path('subjects/', SubjectListCreateAPI.as_view(), name='subject_list_create'),
    path('subjects/<str:section_id>/', SubjectListCreateAPI.as_view(), name='subject_list_by_section'),
    path('org/subjects/<str:organization_id>/', OrgSubjectListAPI.as_view(), name='org-subject-list'),
    path('update/subjects/<str:id>/', SubjectListCreateAPI.as_view(), name='subject-update'),
    path('delete/subjects/<str:id>/', SubjectListCreateAPI.as_view(), name='subject-delete'),
    
    
    path('sections/', SectionListCreateAPI.as_view(), name='section-list'),
    path('sections/<str:class_id>/', SectionListCreateAPI.as_view(), name='section-class'),
    path('sections/update/<str:id>/', SectionListCreateAPI.as_view(), name='section-update'),
    path('sections/delete/<str:id>/', SectionListCreateAPI.as_view(), name='section-delete'),
    path('org/sections/<str:organization_id>/', OrgSectionListAPI.as_view(), name='section-class-list'),

    path('class/<str:id>/', ClassListAll.as_view(), name='class-list-all'),
    path('documents-list/', DocumentListAPI.as_view(), name='document-list'),
    path('documents/<str:id>/', DocumentListAPI.as_view(), name='document-delete'),

    path('generated/exam-id/', GeneratedExamIdAPI.as_view(), name="generated_examId"),
    path('get/exam-id/',ExamIdById.as_view(), name="get_examId"),
    path('update/exam-id/', GeneratedExamIdAPI.as_view(), name="update_examId"),
    path('delete/exam-id/', GeneratedExamIdAPI.as_view(), name="delete_examId"),
    
    path('details-all/', DetailsAllAPI.as_view(), name="details_all"),
    ]