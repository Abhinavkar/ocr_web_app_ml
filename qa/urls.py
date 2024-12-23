from django.urls import path
from . import views


urlpatterns = [
    path('admin/upload/pdf/', views.AdminPdfUpload.as_view(), name='pdf_upload'),
    path('admin/upload/question_image/', views.UserUploadAnswer.as_view(), name='answer_upload'),
    path('admin/upload/pdf/list/',views.AdminPdfGetUpload.as_view(), name='pdf_list'),

    # New Class and Subject APIs
    path('classes/', views.ClassListCreateAPI.as_view(), name='class_api'),
    path('subjects/', views.SubjectListCreateAPI.as_view(), name='subject_api'),
    path('subjects/<str:id>/', views.SubjectListCreateAPI.as_view(), name='subject_api'),
    path('user/upload/answer/pdf/',views.AnswerUploadAPI.as_view(),name="answer_upload")


    ]
