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
from bson import ObjectId
from .utils import extract_text_from_pdf, extract_questions_from_image, get_paragraph_embedding
from sentence_transformers import util
import ast 
from qa.utils import process_uploaded_files
fs = FileSystemStorage() 
from datetime import datetime
import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url



class ResultRetrieveAPI(APIView):
    def get(self, request, object_id=None):
        org_id = request.headers.get('orgId')

        results_collection = get_collection("answers_db")
        

        
        if object_id:
            try:
                object_id = ObjectId(object_id)
                print(f"Querying for ObjectId: {object_id}")
                results = list(results_collection.find({"_id": object_id}))
                # print(f"Query results: {results}")
            except Exception as e:
                return Response({"message": f"Invalid ObjectId: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            results = list(results_collection.find({}))
            # print(f"Query results: {results}")
        
        for result in results:
            result["_id"] = str(result["_id"])  # Convert ObjectId to string
        
        return Response(results, status=status.HTTP_200_OK)
    

class CourseUploadPdfSaveAPI(APIView):
    def post(self, request):     
        try:
            class_id = request.data.get('class_selected')
            subject_id = request.data.get('subject_selected')
            section_id = request.data.get('section_selected')
            pdf_file = request.FILES.get('course_pdf') 
            organization_id = request.data.get('organization')
            user_id = request.headers.get('userId')
            
            if not user_id:
                return Response({"message": "User ID is required."}, status=400)
            
            user_collection = get_collection('auth_users')
            user = user_collection.find_one({"_id": ObjectId(user_id)})
            if not user:
                return Response({"message": "User not found."}, status=404)
            
            if not class_id or not subject_id or not section_id:
                return Response({"message": "Class, Subject, and Section must be selected."}, status=400)
            
            if not pdf_file:
                return Response({"message": "PDF file must be uploaded."}, status=400)
            
            if not pdf_file.name.endswith('.pdf'):
                return Response({"message": "Only PDF files are allowed."}, status=400)
            try:
                upload_result = cloudinary.uploader.upload(pdf_file, resource_type="raw")
                pdf_file_url = upload_result.get("url")
            except Exception as e:
                print("Error uploading PDF to Cloudinary:", str(e))
                return Response({"message": "Internal Server Error while uploading PDF to Cloudinary"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            try:
                organization_collection = get_collection("organization_db")
                organization_name = organization_collection.find_one({"_id": ObjectId(organization_id)})['organization_name']
                if not organization_name:
                    return Response({"message": "Invalid organization ID or Not Found"}, status=400)
            except Exception as e:
                return Response({"message": "Internal Server Error1"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            try:
                classes_collection = get_collection("classes")
                class_name = classes_collection.find_one({"_id": ObjectId(class_id)})['name']
                if not class_name:
                    return Response({"message": "Invalid class ID"}, status=400)
            except Exception as e:
                return Response({"message": "Internal Server Error2"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            try:
                sections_collection = get_collection("sections")
                section_name = sections_collection.find_one({"_id": ObjectId(section_id)})['name']
                if not section_name:
                    return Response({"message": "Invalid section ID"}, status=400)
            except Exception as e:
                return Response({"message": "Internal Server Error3"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            try:
                subjects_collection = get_collection("subjects")
                subject_name = subjects_collection.find_one({"_id": ObjectId(subject_id)})['name']
                if not subject_name:
                    return Response({"message": "Invalid subject ID"}, status=400)
            except Exception as e :
                return Response({"message": "Internal Server Error4"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            current_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            exam_id = f"{organization_name[:3]}_{class_name[:1]}{class_name[-1]}_{section_name[:1]}{section_name[-1]}_{subject_name[:1]}_{current_timestamp}"

            try:
                exam_id_collection = get_collection("examId_db")
                exam_id_collection.insert_one({
                    "_id": exam_id,
                    "organization_id": organization_id,
                    "class_id": class_id,
                    "subject_id": subject_id,
                    "section_id": section_id,
                    "user_id": user_id,
                    "timestamp": current_timestamp,
                    "is_active": True,
                    "course_uploaded": True,
                    "question_uploaded": False
                })
            except Exception as e:
                return Response({"message": "Failed to store exam_id in examId_db."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            pdfs_collection = get_collection("course_pdf")
            pdfs_collection.insert_one({
                "class_id": class_id,
                "subject": subject_id,
                "section": section_id,
                "pdf_file_path": pdf_file_url,
                "exam_id": exam_id,
                "organization_id": organization_id,
                
            })  

            return Response({
                "message": "PDF uploaded successfully.",
                "pdf_file_url": pdf_file_url
            }, status=200)
        except Exception as e:
            return Response({"message": f"An error occurred: {str(e)}"}, status=500)
        except Exception as e:
            return Response({"message": "Invalid upload type or missing file."}, status=400)    



class QuestionPaperUploadSaveAPI(APIView):
    def post(self, request, id=None):
        print(request.data)
        
        try:
            question_pdf = request.FILES.get("question_paper_pdf")
            class_id = request.data.get('class_selected')
            subject_id = request.data.get('subject_selected')
            section_id = request.data.get('section_selected')
            organization_id = request.data.get('organization')
            exam_id = request.data.get('exam_id')
            user_id = request.headers.get('userId')

            print(exam_id)
            
            if not user_id:
                return Response({"message": "User ID is required."}, status=400)
            
            user_collection = get_collection('auth_users')
            user = user_collection.find_one({"_id": ObjectId(user_id)})
            if not user:
                return Response({"message": "User not found."}, status=404)
            
            if not exam_id:
                return Response({"message": "Exam ID must be selected"}, status=400)
            
            if not class_id or not subject_id or not section_id:
                return Response({"message": "Class, Subject, and Section must be selected."}, status=400)
            
            if not question_pdf:
                return Response({"message": "PDF file must be uploaded."}, status=400)
            
            if not question_pdf.name.endswith('.pdf'):
                return Response({"message": "Only PDF files are allowed."}, status=400)

          
            try:
                upload_result = cloudinary.uploader.upload(question_pdf, resource_type="raw")
                print(upload_result)
                pdf_file_url = upload_result.get("secure_url")
            except Exception as e:
                return Response({"message": "Failed to upload PDF to Cloudinary."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            

            try:
                organization_collection = get_collection("organization_db")
                organization_name = organization_collection.find_one({"_id": ObjectId(organization_id)})['organization_name']
                if not organization_name:
                    return Response({"message": "Invalid organization ID or Not Found"}, status=400)
            except Exception as e:
                return Response({"message": "Internal Server Error1"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            try:
                classes_collection = get_collection("classes")
                class_name = classes_collection.find_one({"_id": ObjectId(class_id)})['name']
                if not class_name:
                    return Response({"message": "Invalid class ID"}, status=400)
            except Exception as e:
                return Response({"message": "Internal Server Error2"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            try:
                sections_collection = get_collection("sections")
                section_name = sections_collection.find_one({"_id": ObjectId(section_id)})['name']
                if not section_name:
                    return Response({"message": "Invalid section ID"}, status=400)
            except Exception as e:
                return Response({"message": "Internal Server Error3"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            try:
                subjects_collection = get_collection("subjects")
                subject_name = subjects_collection.find_one({"_id": ObjectId(subject_id)})['name']
                if not subject_name:
                    return Response({"message": "Invalid subject ID"}, status=400)
            except Exception as e:
                return Response({"message": "Internal Server Error4"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            try:
                examId_collection = get_collection("examId_db")
                exam_id = examId_collection.find_one({"_id": exam_id})['_id']
                exam_id = str(exam_id)
                if not exam_id:
                    return Response({"message": "Invalid Exam ID"}, status=400)
            except Exception as e:
                print(e)
                return Response({"message": "Internal Server Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            try:
                examId_collection.update_one(
                    {"_id": exam_id},
                    {"$set": {"question_uploaded": True}}
                )
            except Exception as e:
                return Response({"message": "Failed to update examId_db."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            question_collection = get_collection("question_paper_db")
            question_collection.insert_one({
                "class_id": class_id,
                "subject": subject_id,
                "section": section_id,
                "question_file_url": pdf_file_url,  # Store the Cloudinary URL
                "exam_id": exam_id,
                "organization_id": organization_id,
                "question_pdf": True
            })  

            return Response({
                "message": "Question PDF uploaded successfully.",
                "pdf_file_url": pdf_file_url
            }, status=200)
        except Exception as e:
            return Response({"message": f"An error occurred: {str(e)}"}, status=500)



class AnswerUploadAPI(APIView):
    
    def post(self, request):
        try:
            # Collections
            answers_db_collection = get_collection("answers_db")
            class_collection = get_collection("classes")
            section_collection = get_collection("sections")
            subject_collection = get_collection("subjects")

            # Required fields
            roll_no = request.data.get('rollNo')
            exam_id = request.data.get('examId')
            class_id = request.data.get('classId')
            subject = request.data.get('subjectId')
            section = request.data.get('sectionId')
            answer_pdf = request.FILES.get('answer_pdf')
            organization = request.data.get('organizationId')

            # Validate inputs
            if not roll_no:
                return Response({"error": "Roll number is required"}, status=status.HTTP_400_BAD_REQUEST)
            if not exam_id:
                return Response({"error": "Exam ID is required"}, status=status.HTTP_400_BAD_REQUEST)
            if not class_id:
                return Response({"error": "Class ID is required"}, status=status.HTTP_400_BAD_REQUEST)
            if not subject:
                return Response({"error": "Subject is required"}, status=status.HTTP_400_BAD_REQUEST)
            if not section:
                return Response({"error": "Section is required"}, status=status.HTTP_400_BAD_REQUEST)
            if not answer_pdf:
                return Response({"error": "Answer PDF is required"}, status=status.HTTP_400_BAD_REQUEST)

            # Save PDF file
            try:
                upload_result = cloudinary.uploader.upload(answer_pdf, resource_type="raw")
                pdf_file_url = upload_result.get("secure_url")
            except Exception as e:
                print("Error uploading PDF to Cloudinary:", str(e))
                return Response({"message": "Internal Server Error while uploading PDF to Cloudinary"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Fetch class, section, and subject data
            try:
                class_data = class_collection.find_one({"_id": ObjectId(class_id)})['name']
                if not class_data:
                    return Response({"error": "Invalid class ID"}, status=status.HTTP_400_BAD_REQUEST)

                section_data = section_collection.find_one({'_id': ObjectId(section)})['name']
                if not section_data:
                    return Response({"error": "Invalid section ID"}, status=status.HTTP_400_BAD_REQUEST)

                subject_data = subject_collection.find_one({'_id': ObjectId(subject)})['name']
            except Exception as e:
                print("Error fetching metadata:", str(e))
                return Response({"error": "Error fetching class/section/subject data", "details": str(e)},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Save to answers_db collection
            try:
                answers_db_collection.insert_one({
                    "roll_no": roll_no,
                    "exam_id": exam_id,
                    "class_id": class_id,
                    "subject_id": subject,
                    "section_id": section,
                    "organization_id": organization,
                    "class_name": class_data,
                    "section_name": section_data,
                    "subject_name": subject_data,
                    "answer_pdf_path": pdf_file_url,
                    "is_uploaded": True,
                    "is_evaluated": False,
                    "is_reevaluated": False,
                    "status": "Pending"
                })
                print("Answer PDF details saved to the database.")
            except Exception as e:
                print("Error saving to database:", str(e))
                return Response({"message": "Error saving to database"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({"message": "Answer PDF uploaded successfully"}, status=status.HTTP_201_CREATED)
        except Exception as e:
            print("Unexpected error:", str(e))
            return Response({"message": "Internal server error", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)