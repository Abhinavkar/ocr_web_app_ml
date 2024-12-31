from django.urls import path
from . import views 
from .views import AdminPdfDeleteUpload, AdminQuestionUpload, AnswerRetrieveAPI


urlpatterns = [
    path('admin/upload/pdf/', views.AdminPdfUpload.as_view(), name='pdf_upload'),
    path('admin/upload/question_image/', views.UserUploadAnswer.as_view(), name='answer_upload'),
    path('admin/upload/pdf/list/',views.AdminPdfGetUpload.as_view(), name='pdf_list'),
    # New Class and Subject APIs
    path('user/upload/answer/pdf/',views.AnswerUploadAPI.as_view(),name="answer_upload"),
    path('admin/upload/question-pdf/', AdminQuestionUpload.as_view(), name='admin_upload_question_pdf'),
    path('api/qa/admin/upload/pdf/delete/<str:pdf_name>/', AdminPdfDeleteUpload.as_view(), name='admin-pdf-delete'),
    ]
