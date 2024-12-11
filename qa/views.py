from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.decorators import login_required 
from .utils import process_uploaded_files
from django.core.files.storage import FileSystemStorage
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated , IsAdminUser
from rest_framework.response import Response
from rest_framework import generics, status

# from utils import 

fs=FileSystemStorage()

class AdminPdfUpload(APIView):
    # permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        if request.method == 'POST' and request.FILES['pdf'] and request.FILES['question_image'] :
            pdf_file = request.FILES['pdf']
            pdf_file_path = fs.save(pdf_file.name, pdf_file)
            pdf_file_path = fs.save(pdf_file.name, pdf_file)
            question_image = request.FILES['question_image']
            question_image_path = fs.save(question_image.name, question_image)
            pdf_file_full_path = fs.path(pdf_file_path)
            question_image_full_path = fs.path(question_image_path)


            #Function to be written after ritu's vector db 


            return  Response({'message': 'File Uploaded and Analyzed Sucessfully'}, status=status.HTTP_200_OK)




            # return Response({'result': result}, status=status.HTTP_200_OK)

        else:
            return Response({'message': 'Invalid request'}, status=status.HTTP_400_BAD_REQUEST)
        

class UserUploadAnswer(APIView):
     # permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        if request.method == 'POST' and request.FILES['answer_image'] :
            answer_image = request.FILES['answer_image']
            answer_image_path = fs.save(answer_image.name, answer_image)
            answer_image_full_path = fs.path(answer_image_path)

    
            #Function to be written after ritu's vector db 


            return  Response({'message': 'Answer Uploaded and Analyzed Sucessfully'}, status=status.HTTP_200_OK)
        else :
            return Response({"message":"Invalid Request"},status=status.HTTP_400_BAD_REQUEST)
        








@login_required
def upload_files(request):
    if request.method == 'POST' and request.FILES['pdf'] and request.FILES['question_image'] and request.FILES['answer_image']:
        fs = FileSystemStorage()
        pdf_file = request.FILES['pdf']
        question_image = request.FILES['question_image']
        answer_image = request.FILES['answer_image']
        pdf_file_path = fs.save(pdf_file.name, pdf_file)
        question_image_path = fs.save(question_image.name, question_image)
        answer_image_path = fs.save(answer_image.name, answer_image)
        pdf_file_full_path = fs.path(pdf_file_path)
        question_image_full_path = fs.path(question_image_path)
        answer_image_full_path = fs.path(answer_image_path)
        result = process_uploaded_files(pdf_file_full_path, question_image_full_path, answer_image_full_path)
        return render(request, 'qa/result.html', {'result': result})

    else:
        return render(request, 'qa/upload.html')