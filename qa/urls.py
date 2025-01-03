from django.urls import path
from . import views 
from .views import AdminPdfDeleteUpload, AdminQuestionUpload, ResultRetrieveAPI, AdminPdfGetUpload


urlpatterns = [
    path('admin/upload/pdf/', views.AdminPdfUpload.as_view(), name='pdf_upload'),
    path('admin/upload/pdf/list/', AdminPdfGetUpload.as_view(), name='pdf_list'),
    # New Class and Subject APIs
    path('user/upload/answer/pdf/',views.AnswerUploadAPI.as_view(),name="answer_upload"),
    path('admin/upload/question-pdf/', AdminQuestionUpload.as_view(), name='admin_upload_question_pdf'),
    path('admin/upload/pdf/delete/<str:pdf_name>/', AdminPdfDeleteUpload.as_view(), name='admin-pdf-delete'),
    
    path('results/', ResultRetrieveAPI.as_view(), name='result_list'),
    path('results/<str:object_id>/', ResultRetrieveAPI.as_view(), name='result_detail'),
    ]
