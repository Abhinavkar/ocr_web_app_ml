from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.decorators import login_required 
from .utils import process_uploaded_files
from django.core.files.storage import FileSystemStorage
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated , IsAdminUser
from rest_framework.response import Response
from rest_framework import generics, status
from .utils import *
from .models import Document, Image 
from .models import Class, Subject
from .serializers import ClassSerializer, SubjectSerializer
from rest_framework.permissions import IsAuthenticated, IsAdminUser
    
from authentication.db_wrapper import get_collection
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


fs = FileSystemStorage() 

       
class AdminPdfUpload(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        
        class_selected = request.data.get('class_selected')
        subject_selected = request.data.get('subject_selected')
        pdf_file = request.FILES.get('pdf')  # Safely access the file
        question_image = request.FILES.get('question_image')  # Safely access the file

        if not class_selected or not subject_selected:
            return Response({"message": "Class and Subject must be selected."}, status=400)

        # Prepare response data to include class and subject info
        response_data = {"class": class_selected, "subject": subject_selected}

        # Handle the PDF file upload
        if pdf_file:
            if not pdf_file.name.endswith('.pdf'):
                return Response({"message": "Only PDF files are allowed for course PDF."}, status=400)

            pdf_file_path = fs.save(pdf_file.name, pdf_file)
            pdf_file_full_path = fs.path(pdf_file_path)
            response_data["course_pdf_url"] = pdf_file_full_path

        # Handle the question image upload
        if question_image:
            if not (question_image.name.endswith('.png') or question_image.name.endswith('.jpg') or question_image.name.endswith('.jpeg')):
                return Response({"message": "Only PNG, JPG, or JPEG files are allowed for question paper image."}, status=400)

            question_image_path = fs.save(question_image.name, question_image)
            question_image_full_path = fs.path(question_image_path)
            response_data["question_image_url"] = fs.url(question_image_path)

        # If neither file is uploaded
        if not pdf_file and not question_image:
            return Response({"message": "At least one file (course PDF or question paper image) must be uploaded."}, status=400)

        try:
            if pdf_file:
                pdf_extracted_text = extract_text_from_pdf(pdf_file_full_path)
                

            if question_image:
                question_image_extracted_text = extract_questions_from_image(question_image_full_path)

                
                response_data["question_image_extracted_text"] = question_image_extracted_text
               

            return Response({"message": "Files uploaded successfully.", **response_data}, status=200)

        except Exception as e:
            return Response({"message": f"An error occurred: {str(e)}"}, status=500)
    
    def get(self, request):
        documents = Document.objects.all()  # Get all document entries (adjust the queryset as needed)
        images = Image.objects.all()  # Get all image entries (adjust the queryset as needed)
        
        # Prepare the response data
        document_data = []
        for document in documents:
            document_data.append({
                "id": document.id,
                "pdf_url": fs.url(document.pdf),
                "uploaded_at": document.uploaded_at
            })
        
        image_data = []
        for image in images:
            image_data.append({
                "id": image.id,
                "image_url": fs.url(image.image),
                "uploaded_at": image.uploaded_at
            })
             # Combine documents and images in the response
        return Response({
            "documents": document_data,
            "images": image_data
        })
    
        
        

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
    
    
class ClassListCreateAPI(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        try:
            user, token = JWTAuthentication().authenticate(request)
        except (InvalidToken, TokenError) as e:
            return Response({"Token error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        classes_collection = get_collection("classes")
        classes = list(classes_collection.find({}))
        for cls in classes:
            cls["_id"] = str(cls["_id"])  # Convert ObjectId to string
        return Response(classes, status=status.HTTP_200_OK)

    def post(self, request):
        try:
            user, token = JWTAuthentication().authenticate(request)
        except (InvalidToken, TokenError) as e:
            return Response({"Token error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        data = request.data
        classes_collection = get_collection("classes")
        if classes_collection.find_one({"name": data["name"]}):
            return Response({"error": "Class already exists"}, status=400)
        classes_collection.insert_one(data)
        return Response({"message": "Class created successfully"}, status=status.HTTP_201_CREATED)


class SubjectListCreateAPI(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, id=None):
        try:
            user, token = JWTAuthentication().authenticate(request)
        except (InvalidToken, TokenError) as e:
            return Response({"Token error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        subjects_collection = get_collection("subjects")
        if id:
            subjects = list(subjects_collection.find({"associated_class_id": id}))
        else:
            subjects = list(subjects_collection.find({}))
        for subject in subjects:
            subject["_id"] = str(subject["_id"])  # Convert ObjectId to string
        return Response(subjects, status=status.HTTP_200_OK)

    def post(self, request):
        try:
            user, token = JWTAuthentication().authenticate(request)
        except (InvalidToken, TokenError) as e:
            return Response({"Token error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        data = request.data
        subjects_collection = get_collection("subjects")
        if subjects_collection.find_one({"name": data["name"], "associated_class_id": data["associated_class_id"]}):
            return Response({"error": "Subject already exists for this class"}, status=400)
        subjects_collection.insert_one(data)
        return Response({"message": "Subject created successfully"}, status=status.HTTP_201_CREATED)