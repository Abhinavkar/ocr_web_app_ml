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

fs = FileSystemStorage()  # This will handle the file storage

class AdminPdfUpload(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]  # Ensure user is authenticated and an admin

    def post(self, request):
        class_selected = request.data.get('class_selected')
        subject_selected = request.data.get('subject_selected')
        pdf_file = request.FILES.get('course_pdf')
        question_image = request.FILES.get('question_image')

        if not class_selected or not subject_selected:
            return Response({"message": "Class and Subject must be selected."}, status=400)

        # Prepare response data to include class and subject info
        response_data = {"class": class_selected, "subject": subject_selected}

        # Handle the PDF file upload
        if pdf_file:
            if not pdf_file.name.endswith('.pdf'):
                return Response({"message": "Only PDF files are allowed for course PDF."}, status=400)

            pdf_filename = fs.save(pdf_file.name, pdf_file)  # Save file to file system
            pdf_url = fs.url(pdf_filename)  # Generate URL for the file
            response_data["course_pdf_url"] = pdf_url

        # Handle the question image upload
        if question_image:
            if not (question_image.name.endswith('.png') or question_image.name.endswith('.jpg') or question_image.name.endswith('.jpeg')):
                return Response({"message": "Only PNG, JPG, or JPEG files are allowed for question paper image."}, status=400)

            question_image_filename = fs.save(question_image.name, question_image)
            question_image_url = fs.url(question_image_filename)
            response_data["question_image_url"] = question_image_url

        # If neither PDF nor question image is uploaded, return an error
        if not pdf_file and not question_image:
            return Response({"message": "At least one file (course PDF or question paper image) must be uploaded."}, status=400)

        return Response({"message": "Files uploaded successfully.", **response_data}, status=200)

        

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
        


# @login_required
# def upload_files(request):
#     if request.method == 'POST' and request.FILES['pdf'] and request.FILES['question_image'] and request.FILES['answer_image']:
#         fs = FileSystemStorage()
#         pdf_file = request.FILES['pdf']
#         question_image = request.FILES['question_image']
#         answer_image = request.FILES['answer_image']
#         pdf_file_path = fs.save(pdf_file.name, pdf_file)
#         question_image_path = fs.save(question_image.name, question_image)
#         answer_image_path = fs.save(answer_image.name, answer_image)
#         pdf_file_full_path = fs.path(pdf_file_path)
#         question_image_full_path = fs.path(question_image_path)
#         answer_image_full_path = fs.path(answer_image_path)
#         result = process_uploaded_files(pdf_file_full_path, question_image_full_path, answer_image_full_path)
#         return render(request, 'qa/result.html', {'result': result})

#     else:
#         return render(request, 'qa/upload.html')