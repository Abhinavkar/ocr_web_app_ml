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
from datetime import datetime
import cloudinary
import cloudinary.uploader
from transformers import BertTokenizer, BertModel
import torch
from PyPDF2 import PdfReader
from .utils import extract_text_from_pdf, generate_response 
import json 
from cloudinary.uploader import upload as cloudinary_upload
from together import Together
from .utils import extract_text_from_PDF, evaluate_answers,compute_factual_accuracy,compute_xlmr_similarity,compute_clarity_and_length,extract_answers_from_pdf
from dotenv import load_dotenv
load_dotenv()


# class ResultRetrieveAPI(APIView):
#     def get(self, request, object_id=None):
#         organization_id = request.headers.get('organizationId')
#         if not organization_id:
#             return Response({"message": "Organization ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        
#         results_collection = get_collection("results_db")
#         results_cursor = results_collection.find({"organization_id": organization_id})        
        
#         all_results = []  
#         for result in results_cursor:
#             all_results.extend(result.get("results", []))  
#         json_results = json.dumps(all_results, check_circular=False)
        
#         return Response(json_results, status=status.HTTP_200_OK)




class ResultRetrieveAPI(APIView):
    def get(self, request, object_id=None):
        organization_id = request.headers.get('organizationId')
        if not organization_id:
            return Response({"message": "Organization ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        results_collection = get_collection("results_db")
        results_cursor = results_collection.find({"organization_id": organization_id})
        
        results = []
        for result in results_cursor:
            result["_id"] = str(result["_id"])
              # Convert ObjectId to string
            results.append(result)
        
        response_data = {
            "results": results
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    

    
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
            try:
                organization_collection = get_collection("organization_db")
                organization_name = organization_collection.find_one({"_id": ObjectId(organization_id)})['organization_name']
                if not organization_name:
                    return Response({"message": "Invalid organization ID or Not Found"}, status=404)
            except Exception as e:
                return Response({"message": "Internal Server Error1"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            try:
                classes_collection = get_collection("classes")
                class_name = classes_collection.find_one({"_id": ObjectId(class_id)})['name']
                if not class_name:
                    return Response({"message": "Invalid class ID"}, status=404)
            except Exception as e:
                return Response({"message": "Internal Server Error2"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            try:
                sections_collection = get_collection("sections")
                section_name = sections_collection.find_one({"_id": ObjectId(section_id)})['name']
                if not section_name:
                    return Response({"message": "Invalid section ID"}, status=404)
            except Exception as e:
                return Response({"message": "Internal Server Error3"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            try:
                subjects_collection = get_collection("subjects")
                subject_name = subjects_collection.find_one({"_id": ObjectId(subject_id)})['name']
                if not subject_name:
                    return Response({"message": "Invalid subject ID"}, status=404)
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
                upload_result = cloudinary.uploader.upload(question_pdf, resource_type="raw")
              
                pdf_file_url = upload_result.get("secure_url")
            except Exception as e:
                return Response({"message": "Failed to upload PDF to Cloudinary."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            try:
                course_collection= get_collection("course_pdf")
                course_pdf_url= course_collection.find_one({"exam_id":exam_id})["pdf_file_path"]
                
            except Exception as e :
            
                return Response({"message": "Failed to download course pdf "}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            try:
                question_pdf = requests.get(pdf_file_url)
                if question_pdf.status_code!=200 : 
                    return Response({"message":"Failed to Retrive Question From Exam Id From Cloud"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                course_pdf = requests.get(course_pdf_url)
                if course_pdf.status_code!=200 : 
                    return Response({"message":"Failed to Retrive Course From Exam Id From Cloud"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            except Exception as e :
                 return Response({"message":"Internal server Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            try:
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_question_file:
                    temp_question_file.write(question_pdf.content)
                    temp_question_file_path = temp_question_file.name
                    question_extracted_text = extract_text_from_pdf(temp_question_file_path)
                    os.remove(temp_question_file_path)

                # THis is for Course text extraction 
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf_file:
                    temp_pdf_file.write(course_pdf  .content)
                    temp_pdf_file_path = temp_pdf_file.name
                    course_extracted_text= extract_text_from_pdf(temp_pdf_file_path)
                    os.remove(temp_pdf_file_path)
            except Exception as e:
                return Response({"message": f"Failed to extract text from PDF: {str(e)}"}, status=500)
            try:
                response_text = generate_response(course_extracted_text,question_extracted_text)
                print("Generated Response:", response_text)
            except Exception as e:
                return Response({"message": f"Failed to generate response: {str(e)}"}, status=500)

            
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
                "question_uploaded": True,
                "process_qa":True
                
            })  
        except Exception as e:
            return Response({"message": f"An error occurred: {str(e)}"}, status=500)
        

        try: 
            qamodel= get_collection("process_qa")
            qamodel.insert_one({
                "exam_id":exam_id,
                 "organization_id": organization_id,
                 "processed_answer":response_text,
                 "question_extracted":question_extracted_text
            })
        except Exception as e  : 
            return Response({"message":"Falied to save reponse in Db "}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response({"message": f"Successfully generated answer"}, status=status.HTTP_200_OK)


# ########################################
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
                        return Response({"error": "Organization  is required"}, status=status.HTTP_400_BAD_REQUEST)
                    try:
                        upload_result = cloudinary.uploader.upload(answer_pdf, resource_type="raw")
                        pdf_file_url = upload_result.get("secure_url")
                    except Exception as e:
                        print("Error uploading PDF to Cloudinary:", str(e))
                        return Response({"message": "Internal Server Error while uploading PDF to Cloudinary"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
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
                        return Response({"error": "Error fetching class/section/subject data"},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
                    try:
                        response = requests.get(pdf_file_url)
                        pdf_path = os.path.join("/tmp", answer_pdf.name)  
                        with open(pdf_path, 'wb') as f:
                            f.write(response.content)
                        extracted_text = extract_answers_from_pdf(pdf_path)
                        if not extracted_text:
                            return Response({"error": "The extracted text from the PDF is empty. Please provide a valid PDF."},status=status.HTTP_400_BAD_REQUEST)
                    except Exception as e:
                        return Response({"error": "Error extracting text from PDF:"},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                    # step 2
                    questions_collection=get_collection("process_qa")
                    questions=questions_collection.find_one({"exam_id":exam_id})["question_extracted"]
                    model_answer = questions_collection.find_one({"exam_id":exam_id})["processed_answer"]

                    api_key = os.getenv("TOGETHER_API_KEY")
                    if not api_key:
                        raise ValueError("TOGETHER_API_KEY not found in environment variables")
                    client = Together(api_key=api_key)
                    results = []
                
                    try:
                              final_score=evaluate_answer(extracted_text, model_answer)
                              print(final_score)

                    except Exception as e:
                        return Response({"message": f"An error occurred: {str(e)}"}, status=500)
                    
                    text = final_score

                    pattern = r"Answer (\d+): (\d+)"
                    matches = re.findall(pattern, text)
                    scores_dict = {f"Answer {num}": int(score) for num, score in matches}
                    print(scores_dict)
                    results.append({
                                "question": questions,
                                "user_answer": extracted_text,
                                "model_generated_answer": model_answer,
                                "final_score": final_score,
                                "scores":scores_dict
                            })
                    results_collection=get_collection('results_db')
                    results_collection.insert_one({
                        "results":results,
                        "roll_no":roll_no,
                        "organization_id":organization,
                        "section_id":section,
                        "subject_id":subject,
                        "class_id":class_id,
                        "exam_id":exam_id,
                        "answer_pdf":pdf_file_url,
                        "class_name":class_data,
                        "section_name":section_data,
                        "subject_name":subject_data,
                    })
                    return Response(results, status=status.HTTP_200_OK)
                except Exception as e:
                            return Response({"message": f"An error occurred: {str(e)}"}, status=500)
                          
            
########################################





# class AnswerUploadAPI(APIView):
        
#         def post(self, request):
#             try:
#                 answers_db_collection = get_collection("answers_db")
#                 class_collection = get_collection("classes")
#                 section_collection = get_collection("sections")
#                 subject_collection = get_collection("subjects")
#                 roll_no = request.data.get('rollNo')
#                 exam_id = request.data.get('examId')
#                 class_id = request.data.get('classId')
#                 subject = request.data.get('subjectId')
#                 section = request.data.get('sectionId')
#                 answer_pdf = request.FILES.get('answer_pdf')
#                 organization = request.data.get('organizationId')
#                 if not roll_no:
#                     return Response({"error": "Roll number is required"}, status=status.HTTP_400_BAD_REQUEST)
#                 if not exam_id:
#                     return Response({"error": "Exam ID is required"}, status=status.HTTP_400_BAD_REQUEST)
#                 if not class_id:
#                     return Response({"error": "Class ID is required"}, status=status.HTTP_400_BAD_REQUEST)
#                 if not subject:
#                     return Response({"error": "Subject is required"}, status=status.HTTP_400_BAD_REQUEST)
#                 if not section:
#                     return Response({"error": "Section is required"}, status=status.HTTP_400_BAD_REQUEST)
#                 if not answer_pdf:
#                     return Response({"error": "Answer PDF is required"}, status=status.HTTP_400_BAD_REQUEST)
                
#                 if not organization:
#                     return Response({"error": "Organization  is required"}, status=status.HTTP_400_BAD_REQUEST)
#                 try:
#                     upload_result = cloudinary.uploader.upload(answer_pdf, resource_type="raw")
#                     pdf_file_url = upload_result.get("secure_url")
#                 except Exception as e:
#                     print("Error uploading PDF to Cloudinary:", str(e))
#                     return Response({"message": "Internal Server Error while uploading PDF to Cloudinary"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#                 try:
#                     class_data = class_collection.find_one({"_id": ObjectId(class_id)})['name']
#                     if not class_data:
#                         return Response({"error": "Invalid class ID"}, status=status.HTTP_400_BAD_REQUEST)

#                     section_data = section_collection.find_one({'_id': ObjectId(section)})['name']
#                     if not section_data:
#                         return Response({"error": "Invalid section ID"}, status=status.HTTP_400_BAD_REQUEST)

#                     subject_data = subject_collection.find_one({'_id': ObjectId(subject)})['name']
#                 except Exception as e:
#                     print("Error fetching metadata:", str(e))
#                     return Response({"error": "Error fetching class/section/subject data", "details": str(e)},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                


#                 try:
#                     answers_db_collection.insert_one({
#                         "roll_no": roll_no,
#                         "exam_id": exam_id,
#                         "class_id": class_id,
#                         "subject_id": subject,
#                         "section_id": section,
#                         "organization_id": organization,
#                         "class_name": class_data,
#                         "section_name": section_data,
#                         "subject_name": subject_data,
#                         "answer_pdf_path": pdf_file_url,
#                         "is_uploaded": True,
#                         "is_evaluated": False,
#                         "is_reevaluated": False,
#                         "status": "Pending"
#                     })
#                     print("Answer PDF details saved to the database.")
#                 except Exception as e:
#                     print("Error saving to database:", str(e))
#                     return Response({"message": "Error saving to database"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#                 return Response({"message": "Answer PDF uploaded successfully"}, status=status.HTTP_201_CREATED)
#             except Exception as e:
#                 print("Unexpected error:", str(e))
#                 return Response({"message": "Internal server error", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
            
            
# class ChapterUploadAPI(APIView):
#     def post(self, request):
#         try:
#             class_id = request.data.get('class_selected')
#             subject_id = request.data.get('subject_selected')
#             section_id = request.data.get('section_selected')
#             pdf_file = request.FILES.get('chapter_pdf')
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
#                 upload_result = cloudinary.uploader.upload(pdf_file, resource_type="raw")
#                 pdf_file_url = upload_result.get("url")
#             except Exception as e:
#                 print("Error uploading PDF to Cloudinary:", str(e))
#                 return Response({"message": "Internal Server Error while uploading PDF to Cloudinary"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
#             except Exception as e:
#                 return Response({"message": "Internal Server Error4"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#             exam_id_collection = get_collection("chapterId_db")
#             existing_exam = exam_id_collection.find_one({
#                 "organization_id": organization_id,
#                 "class_id": class_id,
#                 "subject_id": subject_id,
#                 "section_id": section_id,
#                 "examId_generated": True
#             })

#             if existing_exam:
#                 exam_id = existing_exam["_id"]
#             else:
#                 current_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
#                 exam_id = f"{organization_name[:3]}_{class_name[:1]}{class_name[-1]}_{section_name[:1]}{section_name[-1]}_{subject_name[:1]}_{current_timestamp}"

#                 try:
#                     exam_id_collection.insert_one({
#                         "_id": exam_id,
#                         "organization_id": organization_id,
#                         "class_id": class_id,
#                         "subject_id": subject_id,
#                         "section_id": section_id,
#                         "user_id": user_id,
#                         "timestamp": current_timestamp,
#                         "is_active": True,
#                         "chapter_uploaded": True,
#                         "examId_generated": True
#                     })
#                 except Exception as e:
#                     return Response({"message": "Failed to store exam_id in chapterId_db."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#             pdfs_collection = get_collection("chapter_pdf")
#             pdfs_collection.insert_one({
#                 "class_id": class_id,
#                 "subject": subject_id,
#                 "section": section_id,
#                 "pdf_file_path": pdf_file_url,
#                 "exam_id": exam_id,
#                 "organization_id": organization_id,
#             })

#             return Response({
#                 "message": "Chapter PDF uploaded successfully.",
#                 "pdf_file_url": pdf_file_url
#             }, status=200)
#         except Exception as e:
#             return Response({"message": f"An error occurred: {str(e)}"}, status=500)


