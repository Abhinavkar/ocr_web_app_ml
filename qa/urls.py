from django.urls import path
from . import views 
from .views import  ResultRetrieveAPI,AnswerUploadAPI


urlpatterns = [
    # path('admin/upload/pdf/', views.AdminPdfUpload.as_view(), name='pdf_upload'),
      
    path('results/', ResultRetrieveAPI.as_view(), name='result_list'),
    path('results/<str:object_id>/', ResultRetrieveAPI.as_view(), name='result_detail'),
    
    
    path('upload/course/pdf/',views.CourseUploadPdfSaveAPI.as_view(),name="pdf_upload"),
    path('upload/question/pdf/', views.QuestionPaperUploadSaveAPI.as_view(),name="question_upload"),
    
    path('upload/answers/', views.AnswerUploadAPI.as_view(), name="answer_upload"),
    
    ]
