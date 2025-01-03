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

class AdminPdfUpload(APIView):
    def post(self, request):     
        try :
            class_id = request.data.get('class_selected')
            subject = request.data.get('subject_selected')
            section = request.data.get('section_selected')
            pdf_file = request.FILES.get('course_pdf') 
            exam_id = request.data.get('exam_id')
            
            # Debugging statements
            print(f"Received data: class_selected={class_id}, subject_selected={subject}, section_selected={section}")
            
            if not class_id or not subject or not section:
                return Response({"message": "Class, Subject, and Section must be selected."}, status=400)
            
            if not pdf_file:
                return Response({"message": "PDF file must be uploaded."}, status=400)
            
            if not pdf_file.name.endswith('.pdf'):
                return Response({"message": "Only PDF files are allowed."}, status=400)

            fs = FileSystemStorage()
            pdf_file_path = fs.save(pdf_file.name, pdf_file)
            pdf_file_full_path = fs.path(pdf_file_path)
            
            try:
                print("Creating Embeddings for PDF")
                pdf_extracted_text = extract_text_from_pdf(pdf_file_full_path)
                pdf_sentence, pdf_sentence_embeddings = get_paragraph_embedding(pdf_extracted_text)

                pdfs_collection = get_collection("pdf_books")
                pdfs_collection.insert_one({
                    "class_id": class_id,
                    "subject": subject,
                    "section": section,
                    "pdf_file_path": pdf_file_full_path,
                    "pdf_extracted_text": pdf_extracted_text,
                    "pdf_sentence": pdf_sentence,
                    "pdf_sentence_embeddings": pdf_sentence_embeddings.tolist(),
                    "exam_id": exam_id
                })

                return Response({
                    "message": "PDF uploaded successfully.",
                    "pdf_file_url": pdf_file_full_path
                }, status=200)
            except Exception as e:
                return Response({"message": f"An error occurred: {str(e)}"}, status=500)
        except Exception as e:
            return Response({"message": "Invalid upload type or missing file."}, status=400)


class AdminQuestionUpload(APIView):
    def post(self, request):
        # Extract input data from request
        exam_id = request.data.get('exam_id')  # Exam ID
        class_selected = request.data.get('class_selected')  # Class selected
        subject_selected = request.data.get('subject_selected')  # Subject selected
        section_selected = request.data.get('section_selected')  # Section selected
        pdf_file = request.FILES.get('question_image')  # The question PDF file
        
        # Debugging statements
        print(f"Received data: exam_id={exam_id}, class_selected={class_selected}, "
              f"subject_selected={subject_selected}, section_selected={section_selected}")
        
        # Validate that all required fields are provided
        if not exam_id:
            return Response({"message": "Exam ID must be provided."}, status=400)
        
        if not class_selected or not subject_selected or not section_selected:
            return Response({"message": "Class, Subject, and Section must be selected."}, status=400)
        
        if not pdf_file: 
            return Response({"message": "PDF file must be uploaded."}, status=400)
        
        if not pdf_file.name.endswith('.pdf'):
            return Response({"message": "Only PDF files are allowed."}, status=400)

        # Save the uploaded PDF
        fs = FileSystemStorage()
        pdf_file_path = fs.save(pdf_file.name, pdf_file)
        pdf_file_full_path = fs.path(pdf_file_path)
        
        try:
            print("Processing question PDF")
            # Extract text from the uploaded PDF
            pdf_extracted_text = extract_text_from_pdf(pdf_file_full_path)
            # If needed, you could also process this text further here, like generating embeddings
            
            # Get the database collection to store the question data
            question_db_collection = get_collection("question_db")
            
            # Insert the extracted data along with exam_id and other fields into the collection
            question_db_collection.insert_one({
                "exam_id": exam_id,
                "class_id": class_selected,
                "subject": subject_selected,
                "section": section_selected,
                "pdf_file_path": pdf_file_full_path,
                "pdf_extracted_text": pdf_extracted_text,
                # You can add embeddings or other data here if required
            })

            return Response({
                "message": "Question PDF uploaded successfully.",
                "pdf_file_url": pdf_file_full_path
            }, status=200)
        
        except Exception as e:
            # Handle any errors that occur during processing
            return Response({"message": f"An error occurred: {str(e)}"}, status=500)

        # In case of an unexpected scenario
        return Response({"message": "Invalid upload type or missing file."}, status=400)



class AdminPdfGetUpload(APIView):
    def get(self, request):
        try:
            pdfs_collection = get_collection("pdf_books")
            questions_collection = get_collection("question_db")
            classes_collection = get_collection("classes")
            sections_collection = get_collection("sections")
            subjects_collection = get_collection("subjects")

            classes = list(classes_collection.find({}, {"_id": 1, "name": 1}))
            sections = list(sections_collection.find({}, {"_id": 1, "name": 1}))
            subjects = list(subjects_collection.find({}, {"_id": 1, "name": 1}))

            class_map = {str(cls["_id"]): cls["name"] for cls in classes}
            section_map = {str(sec["_id"]): sec["name"] for sec in sections}
            subject_map = {str(sub["_id"]): sub["name"] for sub in subjects}

            pdf_data = list(pdfs_collection.find({}, {
                "class_selected": 1,
                "section_selected": 1,
                "subject_selected": 1,
                "pdf_file_path": 1,
                "_id": 0
            }))

            question_data = list(questions_collection.find({}, {
                "class_selected": 1,
                "section_selected": 1,
                "subject_selected": 1,
                "question_file_path": 1,
                "_id": 0
            }))

            formatted_data = [
                {
                    "class": class_map.get(item["class_selected"], "Unknown Class"),
                    "section": section_map.get(item["section_selected"], "Unknown Section"),
                    "subject": subject_map.get(item["subject_selected"], "Unknown Subject"),
                    "pdf_name": item.get("pdf_file_path", "").split("/")[-1],
                    "question_name": next((q.get("question_file_path", "").split("/")[-1] for q in question_data if q["class_selected"] == item["class_selected"] and q["section_selected"] == item["section_selected"] and q["subject_selected"] == item["subject_selected"]), "N/A")
                }
                for item in pdf_data
            ]

            return Response({"pdf_uploads": formatted_data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"message": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
# class AdminPdfGetUpload(APIView):
#     def get(self, request):
#         try:
#             pdfs_collection = get_collection("pdf_questions")
#             classes_collection = get_collection("classes")
#             subjects_collection = get_collection("subjects")

#             classes = list(classes_collection.find({}, {"_id": 1, "name": 1}))
#             subjects = list(subjects_collection.find({}, {"_id": 1, "name": 1}))

#             class_map = {str(cls["_id"]): cls["name"] for cls in classes}
#             subject_map = {str(sub["_id"]): sub["name"] for sub in subjects}

#             pdf_data = list(pdfs_collection.find({}, {
#                 "class_selected": 1,
#                 "subject_selected": 1,
#                 "pdf_file_path": 1,
#                 "question_image_path": 1,
#                 "_id": 0
#             }))

#             formatted_data = [
#                 {
#                     "class": class_map.get(item["class_selected"], "Unknown Class"),
#                     "subject": subject_map.get(item["subject_selected"], "Unknown Subject"),
#                     "pdf_name": item.get("pdf_file_path", "").split("/")[-1],
#                     "question_name": item.get("question_image_path", "").split("/")[-1]
#                 }
#                 for item in pdf_data
#             ]

#             return Response({"pdf_uploads": formatted_data}, status=status.HTTP_200_OK)

#         except Exception as e:
#             return Response({"message": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class AdminPdfDeleteUpload(APIView):
    def delete(self, request, pdf_file_path):
        try:
            pdfs_collection = get_collection("pdf_questions")
            result = pdfs_collection.delete_one({"pdf_file_path": {"$regex": pdf_file_path}})
            
            if result.deleted_count == 1:
                return Response({"message": "Document deleted successfully."}, status=status.HTTP_200_OK)
            
            return Response({"message": "Document not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"message": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            # If no matching document is found




class ResultRetrieveAPI(APIView):
    def get(self, request, object_id=None):
        results_collection = get_collection("answers_db")
        
        if object_id:
            try:
                object_id = ObjectId(object_id)
                print(f"Querying for ObjectId: {object_id}")
                results = list(results_collection.find({"_id": object_id}))
                print(f"Query results: {results}")
            except Exception as e:
                return Response({"message": f"Invalid ObjectId: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            results = list(results_collection.find({}))
            print(f"Query results: {results}")
        
        for result in results:
            result["_id"] = str(result["_id"])  # Convert ObjectId to string
        
        return Response(results, status=status.HTTP_200_OK)
    

class AnswerUploadAPI(APIView):
    def post(self, request):
        try:
            
            pdfs_collection = get_collection("pdf_books")
            question_db_collection = get_collection("question_db")
            answers_db_collection = get_collection("answers_db")

            
            roll_no = request.data.get('rollNo')
            exam_id = request.data.get('examId')
            class_id = request.data.get('classId')
            subject = request.data.get('subject')
            section = request.data.get('section')
            answer_pdf = request.FILES.get('answer_pdf')

           
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

            
            question_exam_data = question_db_collection.find_one({"exam_id": exam_id})
            if not question_exam_data:
                print("Exam ID not found in question DB")
                return Response({"message": "Exam ID not found in question DB"}, status=status.HTTP_400_BAD_REQUEST)

            pdf_exam_data = pdfs_collection.find_one({"exam_id": exam_id})
            if not pdf_exam_data:
                print("Exam ID not found in PDF collection")
                return Response({"message": "Exam ID not found in PDF collection"}, status=status.HTTP_400_BAD_REQUEST)

            pdf_extracted_text = pdf_exam_data.get("pdf_extracted_text", "")
            pdf_sentence_embeddings = pdf_exam_data.get("pdf_sentence_embeddings", [])
            if not pdf_extracted_text:
                return Response({"message": "Incomplete PDF data"}, status=status.HTTP_400_BAD_REQUEST)

            print("Exam and PDF data fetched successfully.")

            
            try:
                fs = FileSystemStorage()
                filename = f"{exam_id}_{roll_no}_{answer_pdf.name}"
                answer_pdf_path = fs.save(filename, answer_pdf)
                answer_pdf_path = fs.path(answer_pdf_path)
            except Exception as e:
                print("Error saving PDF:", str(e))
                return Response({"message": "Internal Server Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            
            try:
                user_answers = extract_answers_from_pdf(answer_pdf_path)
                if not user_answers:
                    print("Extracted text from the PDF is empty.")
                    return Response({"message": "Extracted text from the PDF is empty"}, status=status.HTTP_400_BAD_REQUEST)
                print("User answers extracted:", user_answers)
            except Exception as e:
                print("Error extracting text from PDF:", str(e))
                return Response({"message": "Error extracting text from PDF"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            
            try:
                answer_embeddings = {
                    question: model.encode(answer_text, convert_to_tensor=True).tolist()
                    for question, answer_text in user_answers.items()
                }
                print("User answer embeddings generated.")
            except Exception as e:
                print("Error generating embeddings:", str(e))
                return Response({"message": "Error generating embeddings"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            
            try:
                # print(f"Fetched question_exam_data: {question_exam_data}")

                question_text = question_exam_data.get("extracted_text", [])
                questions = question_exam_data.get("question_sentence", [])
                question_embeddings = question_exam_data.get("question_sentence_embeddings", [])

                # print(f"Questions: {questions}")
                # print(f"Question Embeddings: {question_embeddings}")

                if not questions or not question_embeddings:
                    print("No questions or embeddings available for the exam.")
                    return Response({"message": "No questions or embeddings available for the exam"}, status=status.HTTP_400_BAD_REQUEST)

                results = []
                for i, (question_text, question_embedding) in enumerate(zip(questions, question_embeddings), start=1):
                    user_answer = user_answers.get(f"Answer {i}", "")
                    if not user_answer:
                        print(f"No user answer for question: {question_text}")
                        continue


                    best_match, question_score, answer_score, relevance = ask_question(
                        paragraph=pdf_extracted_text,
                        user_question=question_text,
                        user_answer=user_answer
                    )

                    print(f"Question: {question_text}")
                    print(f"User Answer: {user_answer}")
                    # print(f"Reference Answer: {best_match}")
                    # print(f"Similarity Score (Question vs. Sentence): {question_score:.2f}%")
                    # print(f"Similarity Score (User Answer vs. Reference): {answer_score:.2f}%")
                    # print(f"Answer Relevance: {relevance}")

                    results.append({
                        "question": question_text,
                        "best_reference_sentence": best_match,
                        "question_similarity_score": question_score,
                        "answer_similarity_score": answer_score,
                        "relevance": relevance,
                    })

                print("Results generated:", results)
                if not results:
                    return Response({"message": "No valid results generated"}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                print("Error processing results:", str(e))
                return Response({"message": "Error processing results", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            
            try:
                answers_db_collection.insert_one({
                    "roll_no": roll_no,
                    "exam_id": exam_id,
                    "exam_id": question_exam_data.get("exam_id"),
                    "class_id": class_id,
                    "subject": subject,
                    "section":section,
                    "user_answers": user_answers,
                    "user_answer_embeddings": answer_embeddings,
                    "results": results
                })
                print("Results inserted into the database.")
            except Exception as e:
                print("Error saving results to database:", str(e))
                return Response({"message": "Error saving results to database"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({"message": "Answers uploaded successfully", "results": results}, status=status.HTTP_201_CREATED)
        except Exception as e:
            print("Unexpected error:", str(e))
            return Response({"message": "Internal server error", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

