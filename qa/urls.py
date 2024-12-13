from django.urls import path
from . import views


urlpatterns = [
    path('admin/upload/pdf/', views.AdminPdfUpload.as_view(), name='pdf_upload'),
    path('admin/upload/question_image/', views.UserUploadAnswer.as_view(), name='answer_upload'),
    path('admin/upload/pdf/list/', views.AdminPdfUpload.as_view(), name='pdf_list'),

    ]
