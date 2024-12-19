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
from authentication.db_wrapper import get_collection

from .utils import extract_text_from_pdf, extract_questions_from_image


fs = FileSystemStorage() 

       
class AdminPdfUpload(APIView):
    def post(self, request):     
        class_selected = request.data.get('class_selected')
        subject_selected = request.data.get('subject_selected')
        pdf_file = request.FILES.get('pdf') 
        question_image = request.FILES.get('question_image')  
        if not class_selected or not subject_selected:
            return Response({"message": "Class and Subject must be selected."}, status=400)
        response_data = {"class": class_selected, "subject": subject_selected}
        fs = FileSystemStorage()
        if pdf_file:
            if not pdf_file.name.endswith('.pdf'):
                return Response({"message": "Only PDF files are allowed for course PDF."}, status=400)
            pdf_file_path = fs.save(pdf_file.name, pdf_file)
            pdf_file_full_path = fs.path(pdf_file_path)
            response_data["course_pdf_url"] = pdf_file_full_path
        if question_image:
            if not (question_image.name.endswith('.png') or question_image.name.endswith('.jpg') or question_image.name.endswith('.jpeg')):
                return Response({"message": "Only PNG, JPG, or JPEG files are allowed for question paper image."}, status=400)

            question_image_path = fs.save(question_image.name, question_image)
            question_image_full_path = fs.path(question_image_path)
            response_data["question_image_url"] = fs.url(question_image_path)
        if not pdf_file and not question_image:
            return Response({"message": "At least one file (course PDF or question paper image) must be uploaded."}, status=400)

        try:
            pdf_extracted_text = None
            question_image_extracted_text = None

            if pdf_file:
                pdf_extracted_text = extract_text_from_pdf(pdf_file_full_path)
                response_data["pdf_extracted_text"] = pdf_extracted_text

            if question_image:
                question_image_extracted_text = extract_questions_from_image(question_image_full_path)
                response_data["question_image_extracted_text"] = question_image_extracted_text

            pdfs_collection = get_collection("pdf_questions")
            
            if pdf_file and question_image:
                pdfs_collection.insert_one({
                    "class_selected": class_selected,
                    "subject_selected": subject_selected,
                    "pdf_file_path": pdf_file_full_path,
                    "pdf_extracted_text": pdf_extracted_text,
                })
            if question_image:
                pdfs_collection.insert_one({
                    "class_selected": class_selected,
                    "subject_selected": subject_selected,
                    "question_image_path": question_image_full_path,
                    "question_image_extracted_text": question_image_extracted_text,
                })

            return Response({"message": "Files uploaded successfully.", **response_data}, status=200)

        except Exception as e:
            return Response({"message": f"An error occurred: {str(e)}"}, status=500)

    def get(self, request):
       
        pdfs_collection = get_collection("pdfs")
        questions_collection = get_collection("questions")

        pdfs = list(pdfs_collection.find({}))
        questions = list(questions_collection.find({}))
        pdf_data = []
        for pdf in pdfs:
            pdf_data.append({
                "id": str(pdf["_id"]),
                "class_selected": pdf["class_selected"],
                "subject_selected": pdf["subject_selected"],
                "pdf_file_path": pdf["pdf_file_path"],
                "pdf_extracted_text": pdf.get("pdf_extracted_text")
            })

        question_data = []
        for question in questions:
            question_data.append({
                "id": str(question["_id"]),
                "class_selected": question["class_selected"],
                "subject_selected": question["subject_selected"],
                "question_image_path": question["question_image_path"],
                "question_image_extracted_text": question.get("question_image_extracted_text")
               
            })
        return Response({"pdfs": pdf_data,"questions": question_data}, status=status.HTTP_200_OK)
    
        
        

class UserUploadAnswer(APIView):
     # permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        if request.method == 'POST' and request.FILES['answer_image'] :
            answer_image = request.FILES['answer_image']
            answer_image_path = fs.save(answer_image.name, answer_image)
            answer_image_full_path = fs.path(answer_image_path)

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
<<<<<<< HEAD
    
=======


>>>>>>> 5b0ed2a6505073a89cc5f1736756ca7361a132d9
    def get(self, request):
        classes_collection = get_collection("classes")
        classes = list(classes_collection.find({}))
        for cls in classes:
            cls["_id"] = str(cls["_id"])  # Convert ObjectId to string
        return Response(classes, status=status.HTTP_200_OK)

    def post(self, request):
<<<<<<< HEAD
       
=======
>>>>>>> 5b0ed2a6505073a89cc5f1736756ca7361a132d9
        data = request.data
        classes_collection = get_collection("classes")
        if classes_collection.find_one({"name": data["name"]}):
            return Response({"error": "Class already exists"}, status=400)
        classes_collection.insert_one(data)
        return Response({"message": "Class created successfully"}, status=status.HTTP_201_CREATED)


class SubjectListCreateAPI(APIView):
<<<<<<< HEAD
  
    def get(self, request, id=None):
        
=======
    
    def get(self, request, id=None):
>>>>>>> 5b0ed2a6505073a89cc5f1736756ca7361a132d9
        subjects_collection = get_collection("subjects")
        if id:
            subjects = list(subjects_collection.find({"associated_class_id": id}))
        else:
            subjects = list(subjects_collection.find({}))
        for subject in subjects:
            subject["_id"] = str(subject["_id"])  # Convert ObjectId to string
        return Response(subjects, status=status.HTTP_200_OK)

    def post(self, request):
        data = request.data
        subjects_collection = get_collection("subjects")
        if subjects_collection.find_one({"name": data["name"], "associated_class_id": data["associated_class_id"]}):
            return Response({"error": "Subject already exists for this class"}, status=400)
        subjects_collection.insert_one(data)
        return Response({"message": "Subject created successfully"}, status=status.HTTP_201_CREATED)


class AnswerUploadAPI(APIView):
    def post(self, request):
        try:
            roll_no = request.data.get('roll_no')
            exam_id = request.data.get('exam_id')
            class_id = request.data.get('class_id')
            subject = request.data.get('subject')
            pdf_file = request.FILES.get('pdf')

            if not all([roll_no, exam_id, class_id, subject, pdf_file]):
                return Response({"error": "All fields are required"}, status=status.HTTP_400_BAD_REQUEST)

            fs = FileSystemStorage()
            pdf_file_path = fs.save(pdf_file.name, pdf_file)
            pdf_file_full_path = fs.path(pdf_file_path)

            answers_collection = get_collection("answers")
            answers_collection.insert_one({
                "roll_no": roll_no,
                "exam_id": exam_id,
                "class_id": class_id,
                "subject": subject,
                "pdf_file_path": pdf_file_full_path,
                "uploaded_by": request.user
            })
        except Exception as e :
            return Response({"message":"Bad Request"} , status=status.HTTP_501_NOT_IMPLEMENTED)

        return Response({"message": "Answer uploaded successfully"}, status=status.HTTP_201_CREATED)
