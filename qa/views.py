from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.decorators import login_required 
from django.core.files.storage import FileSystemStorage
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status
from authentication.db_wrapper import get_collection
from bson import ObjectId
from .utils import extract_text_from_pdf, extract_answers_from_pdf, evaluate_answer, Together
import re
import requests
import tempfile
import os
fs = FileSystemStorage() 
from datetime import datetime, timedelta
from PyPDF2 import PdfReader
from .utils import extract_text_from_pdf, generate_response

from together import Together
from dotenv import load_dotenv
load_dotenv()
import boto3
from datetime import datetime
from  django.conf import settings
from google.cloud import storage

class ResultRetrieveAPI(APIView):
    def get(self, request, object_id=None):
        organization_id = request.headers.get('organizationId')
        if not organization_id:
            return Response({"message": "Organization ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        results_collection = get_collection("results_db")
        results_cursor = results_collection.find({"organization_id": organization_id})
        
        results = []
        for result in results_cursor:
            result["_id"] = str(result["_id"])  # Convert ObjectId to string
            # results.append(result)
            total_score = 0
            question_count = 0
            
            try:
                
                if "results" in result:
                    for res in result["results"]:
                        if "scores" in res:
                            for key, value in res["scores"].items():
                                total_score += value 
                        if "question" in res:
                            
                            question_count += len(re.findall(r'\d+\.', res["question"]))
            except Exception as e:
                print(f"Error processing result: {result['_id']}, error: {str(e)}")
            
            print(f"Total score: {total_score}, Question count: {question_count}")
            
            
            average_score = total_score / question_count if question_count > 0 else 0
            result["total_score"] = total_score
            result["average_score"] = average_score
            
            results.append(result)
            
        
        response_data = {
            "results": results
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    
    def delete(self, request, result_id=None):
        if not result_id:
            return Response({"message": "Result ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        results_collection = get_collection("results_db")
        try:
            result = results_collection.find_one({"_id": ObjectId(result_id)})
            if not result:
                return Response({"message": "Result not found."}, status=status.HTTP_404_NOT_FOUND)
            
            results_collection.delete_one({"_id": ObjectId(result_id)})
            return Response({"message": "Result deleted successfully."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"message": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


 
    
# class CourseUploadPdfSaveAPI(APIView):
#     def post(self, request):     
#         try:
#             class_id = request.data.get('class_selected')
#             subject_id = request.data.get('subject_selected')
#             section_id = request.data.get('section_selected')
#             pdf_file = request.FILES.get('course_pdf') 
#             organization_id = request.data.get('organization')
#             user_id = request.headers.get('userId')
            
#             if not user_id:
#                 return Response({"message": "User ID is required."}, status=400)
            
#             user_collection = get_collection('auth_users')
#             user = user_collection.find_one({"_id": ObjectId(user_id)})
#             if not user:
#                 return Response({"message": "User not found."}, status=404)
            
#             if not class_id or not subject_id or not section_id:
#                 return Response({"message": "Class, Subject, and Section must be selected."}, status=400)
            
#             if not pdf_file:
#                 return Response({"message": "PDF file must be uploaded."}, status=400)
            
#             if not pdf_file.name.endswith('.pdf'):
#                 return Response({"message": "Only PDF files are allowed."}, status=400)
#             try:
#                 client = storage.Client()
#                 bucket = client.bucket("dev-inc-swebucket")

#                 # Generate unique blob name
#                 blob_name = f"course_pdf/{pdf_file.name}"
#                 blob = bucket.blob(blob_name)

#                 # Use upload_from_file for InMemoryUploadedFile
#                 blob.upload_from_file(pdf_file, content_type="application/pdf")

#                 pdf_file_url = f"gs://dev-inc-swebucket/{blob_name}"
                
                
                
                
#                 pdf_file_url = blob.generate_signed_url(
#                     version="v4",
#                     expiration=timedelta(hours=24),
#                     method="GET"
#                 )
                

                

#             except Exception as e:
#                 print("Error uploading PDF to GCS:", str(e))
#                 return Response({"message": "Internal Server Error while uploading PDF to GCS"},
#                                 status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#             try:
#                 organization_collection = get_collection("organization_db")
#                 organization_name = organization_collection.find_one({"_id": ObjectId(organization_id)})['organization_name']
#                 if not organization_name:
#                     return Response({"message": "Invalid organization ID or Not Found"}, status=400)
#             except Exception as e:
#                 return Response({"message": "Internal Server Error1"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#             try:
#                 classes_collection = get_collection("classes")
#                 class_name = classes_collection.find_one({"_id": ObjectId(class_id)})['name']
#                 if not class_name:
#                     return Response({"message": "Invalid class ID"}, status=400)
#             except Exception as e:
#                 return Response({"message": "Internal Server Error2"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#             try:
#                 sections_collection = get_collection("sections")
#                 section_name = sections_collection.find_one({"_id": ObjectId(section_id)})['name']
#                 if not section_name:
#                     return Response({"message": "Invalid section ID"}, status=400)
#             except Exception as e:
#                 return Response({"message": "Internal Server Error3"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#             try:
#                 subjects_collection = get_collection("subjects")
#                 subject_name = subjects_collection.find_one({"_id": ObjectId(subject_id)})['name']
#                 if not subject_name:
#                     return Response({"message": "Invalid subject ID"}, status=400)
#             except Exception as e :
#                 return Response({"message": "Internal Server Error4"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
#             current_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
#             exam_id = f"{organization_name[:3]}_{class_name[:1]}{class_name[-1]}_{section_name[:1]}{section_name[-1]}_{subject_name[:1]}_{current_timestamp}"

#             try:
#                 exam_id_collection = get_collection("examId_db")
#                 exam_id_collection.insert_one({
#                     "_id": exam_id,
#                     "organization_id": organization_id,
#                     "class_id": class_id,
#                     "subject_id": subject_id,
#                     "section_id": section_id,
#                     "user_id": user_id,
#                     "timestamp": current_timestamp,
#                     "is_active": True,
#                     "course_uploaded": True,
#                     "question_uploaded": False
#                 })
#             except Exception as e:
#                 return Response({"message": "Failed to store exam_id in examId_db."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#             pdfs_collection = get_collection("course_pdf")
#             pdfs_collection.insert_one({
#                 "class_id": class_id,
#                 "subject": subject_id,
#                 "section": section_id,
#                 "pdf_file_path": pdf_file_url,
#                 "exam_id": exam_id,
#                 "organization_id": organization_id,
                
#             })  

#             return Response({
#                 "message": "PDF uploaded successfully.",
#                 "pdf_file_url": pdf_file_url
#             }, status=200)
#         except Exception as e:
#             return Response({"message": f"An error occurred: {str(e)}"}, status=500)
#         except Exception as e:
#             return Response({"message": "Invalid upload type or missing file."}, status=400)    


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
                client = storage.Client()
                bucket = client.bucket("dev-inc-swebucket")

                # Generate unique blob name
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                blob_name = f"course_pdf/{timestamp}_{pdf_file.name}"
                blob = bucket.blob(blob_name)

                # Upload file
                blob.upload_from_file(pdf_file, content_type="application/pdf")

                # Actual GCS blob path
                pdf_file_path = f"gs://dev-inc-swebucket/{blob_name}"

                # Generate signed URL
                pdf_file_signed_url = blob.generate_signed_url(
                    version="v4",
                    expiration=timedelta(hours=24),
                    method="GET"
                )

            except Exception as e:
                print("Error uploading PDF to GCS:", str(e))
                return Response({"message": "Internal Server Error while uploading PDF to GCS"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
                "exam_id": exam_id,
                "organization_id": organization_id,
                "pdf_file_path": pdf_file_path,  # ✅ Actual GCS blob path
                "pdf_file_signed_url": pdf_file_signed_url  # ✅ For frontend use
            })  

            return Response({
                "message": "PDF uploaded successfully.",
                "pdf_file_url": pdf_file_signed_url  # Returning signed URL to frontend
            }, status=200)
        except Exception as e:
            return Response({"message": f"An error occurred: {str(e)}"}, status=500)
        except Exception as e:
            return Response({"message": "Invalid upload type or missing file."}, status=400)



# class QuestionPaperUploadSaveAPI(APIView):
#     def post(self, request, id=None):
#         try:
#             question_pdf = request.FILES.get("question_paper_pdf")
#             class_id = request.data.get('class_selected')
#             subject_id = request.data.get('subject_selected')
#             section_id = request.data.get('section_selected')
#             organization_id = request.data.get('organization')
#             exam_id = request.data.get('exam_id')
#             user_id = request.headers.get('userId')

#             if not user_id:
#                 return Response({"message": "User ID is required."}, status=400)

#             # Validate User Existence
#             user_collection = get_collection('auth_users')
#             user = user_collection.find_one({"_id": ObjectId(user_id)})
#             if not user:
#                 return Response({"message": "User not found."}, status=404)

#             if not exam_id:
#                 return Response({"message": "Exam ID must be selected"}, status=400)

#             if not class_id or not subject_id or not section_id:
#                 return Response({"message": "Class, Subject, and Section must be selected."}, status=400)

#             if not question_pdf:
#                 return Response({"message": "PDF file must be uploaded."}, status=400)

#             if not question_pdf.name.endswith('.pdf'):
#                 return Response({"message": "Only PDF files are allowed."}, status=400)

#             # Validate Organization, Class, Section, and Subject
#             organization_collection = get_collection("organization_db")
#             organization_name = organization_collection.find_one({"_id": ObjectId(organization_id)})['organization_name']
#             if not organization_name:
#                 return Response({"message": "Invalid organization ID or Not Found"}, status=404)

#             classes_collection = get_collection("classes")
#             class_name = classes_collection.find_one({"_id": ObjectId(class_id)})['name']
#             if not class_name:
#                 return Response({"message": "Invalid class ID"}, status=404)

#             sections_collection = get_collection("sections")
#             section_name = sections_collection.find_one({"_id": ObjectId(section_id)})['name']
#             if not section_name:
#                 return Response({"message": "Invalid section ID"}, status=404)

#             subjects_collection = get_collection("subjects")
#             subject_name = subjects_collection.find_one({"_id": ObjectId(subject_id)})['name']
#             if not subject_name:
#                 return Response({"message": "Invalid subject ID"}, status=404)

#             # Validate Exam ID
#             examId_collection = get_collection("examId_db")
#             exam_record = examId_collection.find_one({"_id": exam_id})
#             if not exam_record:
#                 print("Invalid Exam ID")
#                 return Response({"message": "Invalid Exam ID"}, status=400)


#             try:
#                 s3_client = boto3.client(
#                     's3',
#                     aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
#                     aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
#                     region_name=os.getenv("AWS_S3_REGION_NAME")
#                 )

#                 file_key = f"question_papers/{datetime.now().strftime('%Y%m%d%H%M%S')}_{question_pdf.name}"
#                 bucket_name = os.getenv("AWS_STORAGE_BUCKET_NAME")

#                 # Upload Question PDF to AWS S3
#                 s3_client.upload_fileobj(question_pdf, bucket_name, file_key)

#                 # Generate file URL
#                 question_file_url = f"https://{bucket_name}.s3.{os.getenv('AWS_S3_REGION_NAME')}.amazonaws.com/{file_key}"

#             except Exception as e:
#                 print("Error uploading PDF to AWS", str(e))
#                 return Response({"message": "Failed to upload PDF to AWS S3."}, status=500)

#             # Download course PDF from S3 (as done previously)
#             try:
#                 course_collection = get_collection("course_pdf")
#                 course_pdf_url = course_collection.find_one({"exam_id": exam_id})["pdf_file_path"]

#                 # Retrieve PDFs
#                 question_pdf_response = requests.get(question_file_url)
#                 course_pdf_response = requests.get(course_pdf_url)

#                 if question_pdf_response.status_code != 200:
#                     return Response({"message": "Failed to retrieve question paper from S3"}, status=500)

#                 if course_pdf_response.status_code != 200:
#                     return Response({"message": "Failed to retrieve course PDF from S3"}, status=500)

#             except Exception as e:
#                 print("Error retrieving PDFs:", str(e))
#                 return Response({"message": "Error retrieving PDFs."}, status=500)

#             # Extract text from the PDFs
#             try:
#                 with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_question_file:
#                     temp_question_file.write(question_pdf_response.content)
#                     temp_question_file_path = temp_question_file.name
#                     question_extracted_text = extract_text_from_pdf(temp_question_file_path)
#                     os.remove(temp_question_file_path)

#                 with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_course_file:
#                     temp_course_file.write(course_pdf_response.content)
#                     temp_course_file_path = temp_course_file.name
#                     course_extracted_text = extract_text_from_pdf(temp_course_file_path)
#                     os.remove(temp_course_file_path)

#             except Exception as e:
#                 print("Error extracting text from PDFs:", str(e))
#                 return Response({"message": f"Failed to extract text from PDFs: {str(e)}"}, status=500)

#             # Generate response text based on extracted texts
#             try:
#                 response_text = generate_response(course_extracted_text, question_extracted_text)
#             except Exception as e:
#                 print("Error generating response:", str(e))
#                 return Response({"message": f"Failed to generate response: {str(e)}"}, status=500)

#             # Update exam record to indicate question uploaded
#             try:
#                 examId_collection.update_one(
#                     {"_id": exam_id},
#                     {"$set": {"question_uploaded": True}}
#                 )
#             except Exception as e:
#                 print("Error updating exam record:", str(e))
#                 return Response({"message": "Failed to update exam record."}, status=500)

#             # Save question paper info to database
#             question_collection = get_collection("question_paper_db")
#             question_collection.insert_one({
#                 "class_id": class_id,
#                 "subject": subject_id,
#                 "section": section_id,
#                 "question_file_url": question_file_url,  # Store the AWS S3 URL
#                 "exam_id": exam_id,
#                 "organization_id": organization_id,
#                 "question_uploaded": True,
#                 "process_qa": True
#             })

#             # Save processed response in the QA collection
#             qamodel = get_collection("process_qa")
#             qamodel.insert_one({
#                 "exam_id": exam_id,
#                 "organization_id": organization_id,
#                 "processed_answer": response_text,
#                 "question_extracted": question_extracted_text
#             })

#             return Response({"message": "Successfully generated answer and uploaded question paper."}, status=200)

#         except Exception as e:
#             return Response({"message": f"An error occurred: {str(e)}"}, status=500)


class QuestionPaperUploadSaveAPI(APIView):
    def post(self, request, id=None):
        try:
            question_pdf = request.FILES.get("question_paper_pdf")
            class_id = request.data.get('class_selected')
            subject_id = request.data.get('subject_selected')
            section_id = request.data.get('section_selected')
            organization_id = request.data.get('organization')
            exam_id = request.data.get('exam_id')
            user_id = request.headers.get('userId')

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

            organization_collection = get_collection("organization_db")
            organization_name = organization_collection.find_one({"_id": ObjectId(organization_id)})['organization_name']
            if not organization_name:
                return Response({"message": "Invalid organization ID or Not Found"}, status=404)

            class_name = get_collection("classes").find_one({"_id": ObjectId(class_id)})['name']
            section_name = get_collection("sections").find_one({"_id": ObjectId(section_id)})['name']
            subject_name = get_collection("subjects").find_one({"_id": ObjectId(subject_id)})['name']

            examId_collection = get_collection("examId_db")
            exam_record = examId_collection.find_one({"_id": exam_id})
            if not exam_record:
                return Response({"message": "Invalid Exam ID"}, status=400)

            # Upload to GCS
            try:
                client = storage.Client()
                bucket = client.bucket("dev-inc-swebucket")

                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                blob_name = f"question_papers/{timestamp}_{question_pdf.name}"
                blob = bucket.blob(blob_name)
                blob.upload_from_file(question_pdf, content_type="application/pdf")

                question_file_path = f"gs://dev-inc-swebucket/{blob_name}"
                question_file_signed_url = blob.generate_signed_url(
                    version="v4",
                    expiration=timedelta(hours=24),
                    method="GET"
                )

            except Exception as e:
                print("Error uploading PDF to GCS:", str(e))
                return Response({"message": "Failed to upload PDF to Google Cloud Storage."}, status=500)

            # Retrieve Course PDF from GCS
            try:
                course_collection = get_collection("course_pdf")
                course_pdf_url = course_collection.find_one({"exam_id": exam_id})["pdf_file_path"]

                question_blob = bucket.blob(blob_name)
                question_pdf_content = question_blob.download_as_bytes()

                course_blob = bucket.blob(course_pdf_url.replace("gs://dev-inc-swebucket/", ""))
                course_pdf_content = course_blob.download_as_bytes()

            except Exception as e:
                print("Error retrieving PDFs:", str(e))
                return Response({"message": "Error retrieving PDFs from GCS."}, status=500)

            # Extract text
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_question_file:
                    temp_question_file.write(question_pdf_content)
                    question_extracted_text = extract_text_from_pdf(temp_question_file.name)
                    os.remove(temp_question_file.name)

                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_course_file:
                    temp_course_file.write(course_pdf_content)
                    course_extracted_text = extract_text_from_pdf(temp_course_file.name)
                    os.remove(temp_course_file.name)

            except Exception as e:
                print("Error extracting text from PDFs:", str(e))
                return Response({"message": f"Failed to extract text from PDFs: {str(e)}"}, status=500)

            # Generate response
            try:
                response_text = generate_response(course_extracted_text, question_extracted_text)
            except Exception as e:
                print("Error generating response:", str(e))
                return Response({"message": f"Failed to generate response: {str(e)}"}, status=500)

            # Update exam record
            examId_collection.update_one(
                {"_id": exam_id},
                {"$set": {"question_uploaded": True}}
            )

            # Save question paper metadata
            question_collection = get_collection("question_paper_db")
            question_collection.insert_one({
                "class_id": class_id,
                "subject": subject_id,
                "section": section_id,
                "question_file_path": question_file_path,  
                "question_file_signed_url": question_file_signed_url,  
                "exam_id": exam_id,
                "organization_id": organization_id,
                "question_uploaded": True,
                "process_qa": True
            })

            # Save processed QA
            qamodel = get_collection("process_qa")
            qamodel.insert_one({
                "exam_id": exam_id,
                "organization_id": organization_id,
                "processed_answer": response_text,
                "question_extracted": question_extracted_text
            })

            return Response({
                "message": "Successfully generated answer and uploaded question paper.",
                "question_file_url": question_file_signed_url  
            }, status=200)

        except Exception as e:
            return Response({"message": f"An error occurred: {str(e)}"}, status=500)
# class AnswerUploadAPI(APIView):
        
#         def post(self, request):
                
#                 try:
                 
#                     answers_db_collection = get_collection("answers_db")
#                     class_collection = get_collection("classes")
#                     section_collection = get_collection("sections")
#                     subject_collection = get_collection("subjects")
#                     roll_no = request.data.get('rollNo')
#                     exam_id = request.data.get('examId')
#                     class_id = request.data.get('classId')
#                     subject = request.data.get('subjectId')
#                     section = request.data.get('sectionId')
#                     answer_pdf = request.FILES.get('answer_pdf')
#                     organization = request.data.get('organizationId')
#                     if not roll_no:
#                         return Response({"error": "Roll number is required"}, status=status.HTTP_400_BAD_REQUEST)
#                     if not exam_id:
#                         return Response({"error": "Exam ID is required"}, status=status.HTTP_400_BAD_REQUEST)
#                     if not class_id:
#                         return Response({"error": "Class ID is required"}, status=status.HTTP_400_BAD_REQUEST)
#                     if not subject:
#                         return Response({"error": "Subject is required"}, status=status.HTTP_400_BAD_REQUEST)
#                     if not section:
#                         return Response({"error": "Section is required"}, status=status.HTTP_400_BAD_REQUEST)
#                     if not answer_pdf:
#                         return Response({"error": "Answer PDF is required"}, status=status.HTTP_400_BAD_REQUEST)
                    
#                     if not organization:
#                         return Response({"error": "Organization  is required"}, status=status.HTTP_400_BAD_REQUEST)
#                     try:
                         
#                                 s3_client = boto3.client(
#                                     's3',
#                                     aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
#                                     aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
#                                     region_name=os.getenv("AWS_S3_REGION_NAME")
#                                 )

#                                 file_key = f"question_papers/{datetime.now().strftime('%Y%m%d%H%M%S')}_{answer_pdf.name}"
#                                 bucket_name = os.getenv("AWS_STORAGE_BUCKET_NAME")
#                                 s3_client.upload_fileobj(answer_pdf, bucket_name, file_key)
#                                 upload_result = f"https://{bucket_name}.s3.{os.getenv('AWS_S3_REGION_NAME')}.amazonaws.com/{file_key}"
                                
#                                 pdf_file_url = upload_result
#                     except Exception as e:
#                         print("Error uploading PDF to S3:", str(e))
#                         return Response({"message": "Internal Server Error while uploading PDF to S3"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#                     try:
#                         class_data = class_collection.find_one({"_id": ObjectId(class_id)})['name']
#                         if not class_data:
#                             return Response({"error": "Invalid class ID"}, status=status.HTTP_400_BAD_REQUEST)

#                         section_data = section_collection.find_one({'_id': ObjectId(section)})['name']
#                         if not section_data:
#                             return Response({"error": "Invalid section ID"}, status=status.HTTP_400_BAD_REQUEST)

#                         subject_data = subject_collection.find_one({'_id': ObjectId(subject)})['name']
#                     except Exception as e:
#                         print("Error fetching metadata:", str(e))
#                         return Response({"error": "Error fetching class/section/subject data"},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
#                     try:
#                         response = requests.get(pdf_file_url)
#                         pdf_path = os.path.join("/tmp", answer_pdf.name)  
#                         with open(pdf_path, 'wb') as f:
#                             f.write(response.content)
#                         extracted_text = extract_answers_from_pdf(pdf_path)
#                         if not extracted_text:
#                             return Response({"error": "The extracted text from the PDF is empty. Please provide a valid PDF."},status=status.HTTP_400_BAD_REQUEST)
#                     except Exception as e:
#                         print("Error extracting text from PDF:", str(e))
#                         return Response({"error": "Ocr extraction failed :"},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#                     try:
#                         questions_collection=get_collection("process_qa")
#                         try : 
#                           questions=questions_collection.find_one({"exam_id":exam_id})["question_extracted"]
#                         except Exception as e:
#                             print("Error fetching questions:", str(e))
#                             return Response({"error": "Error fetching questions"},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#                         try :
#                             model_answer = questions_collection.find_one({"exam_id":exam_id})["processed_answer"]
#                         except Exception as e:
#                             print("Error fetching model answers:", str(e))
#                             return Response({"error": "Error fetching model answers"},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#                     except Exception as e:
#                         print("Error fetching questions and model answers:", str(e))
#                         return Response({"error": "Error fetching questions and model answers"},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#                     try:
#                         api_key = os.getenv("TOGETHER_API_KEY")
#                         if not api_key:
#                             raise ValueError("TOGETHER_API_KEY not found in environment variables")
#                         client = Together(api_key=api_key)
#                     except Exception as e:  
#                         print("Error initializing Together client:", str(e))
#                         return Response({"error": "Error initializing Together client"},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                    
#                     results = []
                
#                     try:
#                               final_score=evaluate_answer(extracted_text, model_answer)
#                               final_score = final_score.replace('{', '').replace('}', '').replace('*', '').replace('```', '').replace('\t','').replace('"','')
#                               print(final_score)

#                     except Exception as e:
#                         print("Error evaluating answer:", str(e))
#                         return Response({"message": f"An error occurred: {str(e)}"}, status=500)
#                     try: 
#                             text = final_score

#                             results.append({
#                                         "question": questions,
#                                         "user_answer": extracted_text,
#                                         "model_generated_answer": model_answer,
#                                         "final_score": final_score,
#                                     })
#                             results_collection=get_collection('results_db')
#                             results_collection.insert_one({
#                                 "results":results,
#                                 "roll_no":roll_no,
#                                 "organization_id":organization,
#                                 "section_id":section,
#                                 "subject_id":subject,
#                                 "class_id":class_id,
#                                 "exam_id":exam_id,
#                                 "answer_pdf":pdf_file_url,
#                                 "class_name":class_data,
#                                 "section_name":section_data,
#                                 "subject_name":subject_data,
#                                 "final_score":final_score,
#                             })
#                             return Response(results, status=status.HTTP_200_OK)
#                     except Exception as e:
#                             print("Error evaluating final score :", str(e))
#                             return Response({"message": f"An error occurred: {str(e)}"}, status=500)
#                 except Exception as e:
#                             print("Error extracting text from PDF jhsdbvushb :", str(e))
#                             return Response({"message": f"An error occurred: {str(e)}"}, status=500)





class AnswerUploadAPI(APIView):
        
    def post(self, request):
        try:
            answers_db_collection = get_collection("answers_db")
            class_collection = get_collection("classes")
            section_collection = get_collection("sections")
            subject_collection = get_collection("subjects")
            roll_no = request.data.get('rollNo')
            exam_id = request.data.get('examId')
            class_id = request.data.get('classId')
            subject = request.data.get('subjectId')
            section = request.data.get('sectionId')
            answer_pdf = request.FILES.get('answer_pdf')
            organization = request.data.get('organizationId')

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
            if not organization:
                return Response({"error": "Organization is required"}, status=status.HTTP_400_BAD_REQUEST)

            
            try:
                client = storage.Client()
                bucket = client.bucket("dev-inc-swebucket")

                # Generate unique blob name
                blob_name = f"answers/{answer_pdf.name}"
                blob = bucket.blob(blob_name)

                # Use upload_from_file for InMemoryUploadedFile
                blob.upload_from_file(answer_pdf, content_type="application/pdf")

                pdf_file_url = f"gs://dev-inc-swebucket/{blob_name}"

            except Exception as e:
                print("Error uploading PDF to GCS:", str(e))
                return Response({"message": "Internal Server Error while uploading PDF to GCS"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
                return Response({"error": "Error fetching class/section/subject data"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            try:
                
                client = storage.Client()
                bucket = client.bucket("dev-inc-swebucket")
                blob = bucket.blob(f"answers/{answer_pdf.name}")

                pdf_path = os.path.join("/tmp", answer_pdf.name)
                blob.download_to_filename(pdf_path)

                extracted_text = extract_answers_from_pdf(pdf_path)
                if not extracted_text:
                    return Response({"error": "The extracted text from the PDF is empty. Please provide a valid PDF."}, status=status.HTTP_400_BAD_REQUEST)
                
                answers_db_collection.insert_one({
                "exam_id": exam_id,
                "roll_no": roll_no,
                "organization_id": organization,
                "section_id": section,
                "subject_id": subject,
                "class_id": class_id,
                "answer_pdf": pdf_file_url,
                "extracted_text": extracted_text,
                "created_at": datetime.now()
            })
            except Exception as e:
                print("Error extracting text from PDF:", str(e))
                return Response({"error": "OCR extraction failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            try:
                questions_collection = get_collection("process_qa")
                try:
                    questions = questions_collection.find_one({"exam_id": exam_id})["question_extracted"]
                except Exception as e:
                    print("Error fetching questions:", str(e))
                    return Response({"error": "Error fetching questions"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                try:
                    model_answer = questions_collection.find_one({"exam_id": exam_id})["processed_answer"]
                except Exception as e:
                    print("Error fetching model answers:", str(e))
                    return Response({"error": "Error fetching model answers"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            except Exception as e:
                print("Error fetching questions and model answers:", str(e))
                return Response({"error": "Error fetching questions and model answers"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            try:
                api_key = os.getenv("TOGETHER_API_KEY")
                if not api_key:
                    raise ValueError("TOGETHER_API_KEY not found in environment variables")
                client = Together(api_key=api_key)
            except Exception as e:
                print("Error initializing Together client:", str(e))
                return Response({"error": "Error initializing Together client"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            results = []

            try:
                final_score = evaluate_answer(extracted_text, model_answer)
                final_score = final_score.replace('{', '').replace('}', '').replace('*', '').replace('```', '').replace('\t', '').replace('"', '')
                print(final_score)
            except Exception as e:
                print("Error evaluating answer:", str(e))
                return Response({"message": f"An error occurred: {str(e)}"}, status=500)

            try:
                text = final_score

                results.append({
                    "question": questions,
                    "user_answer": extracted_text,
                    "model_generated_answer": model_answer,
                    "final_score": final_score,
                })
                
                # Fetch questions from process_qa collection
                process_qa_collection = get_collection("process_qa")
                questions_data = process_qa_collection.find_one({"exam_id": exam_id})

                if questions_data and "question_extracted" in questions_data:
                    raw_questions = questions_data["question_extracted"]
                    
                    # Process to remove excessive newlines and join words properly
                    cleaned_questions = " ".join(raw_questions.split()).replace(" .", ".")

                    print("\n*** Questions Extracted from process_qa ***\n")
                    print(cleaned_questions)
                else:
                    print("\nNo questions found for the given exam ID\n")

               
                # Extract scores and calculate the total obtained score
                score_pattern = re.findall(r"score:\s*(\d+)(?:/(\d+))?", final_score)

                total_obtained_score = 0
                formatted_scores = []

                for score in score_pattern:
                    obtained = int(score[0])  # Extract obtained marks
                    total = int(score[1]) if score[1] else None  # Extract total marks if available

                    total_obtained_score += obtained  # Sum up obtained marks

                    # Store in "X/Y" format if total is available; otherwise, just store "X"
                    formatted_scores.append(f"{obtained}/{total}" if total else f"{obtained}")

                
                
                results_collection = get_collection('results_db')
                results_collection.insert_one({
                    "results": results,
                    "roll_no": roll_no,
                    "organization_id": organization,
                    "section_id": section,
                    "subject_id": subject,
                    "class_id": class_id,
                    "exam_id": exam_id,
                    "answer_pdf": pdf_file_url,
                    "class_name": class_data,
                    "section_name": section_data,
                    "subject_name": subject_data,
                    "final_score": final_score,
                    "total_obtained_score": total_obtained_score,  # Store total score
                })
                return Response(results, status=status.HTTP_200_OK)
            except Exception as e:
                print("Error evaluating final score:", str(e))
                return Response({"message": f"An error occurred: {str(e)}"}, status=500)
        except Exception as e:
            print("Error extracting text from PDF:", str(e))
            return Response({"message": f"An error occurred: {str(e)}"}, status=500)








            # try:
            #     s3_client = boto3.client(
            #         's3',
            #         aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            #         aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            #         region_name=os.getenv("AWS_S3_REGION_NAME")
            #     )

            #     file_key = f"question_papers/{datetime.now().strftime('%Y%m%d%H%M%S')}_{answer_pdf.name}"
            #     bucket_name = os.getenv("AWS_STORAGE_BUCKET_NAME")
            #     s3_client.upload_fileobj(answer_pdf, bucket_name, file_key)
            #     upload_result = f"https://{bucket_name}.s3.{os.getenv('AWS_S3_REGION_NAME')}.amazonaws.com/{file_key}"

            #     pdf_file_url = upload_result
            # except Exception as e:
            #     print("Error uploading PDF to S3:", str(e))
            #     return Response({"message": "Internal Server Error while uploading PDF to S3"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            
            
