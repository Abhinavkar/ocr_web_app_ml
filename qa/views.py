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

from .utils import extract_text_from_pdf, extract_questions_from_image, get_paragraph_embedding
from sentence_transformers import util
import ast 

fs = FileSystemStorage() 
class AdminPdfGetUpload(APIView):
    def get(self, request):
        try:
            pdfs_collection = get_collection("pdf_questions")
            print(pdfs_collection)
            # return Response({"pdfs": pdf_data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"message": f"An error occurred: {str(e)}"}, status=500)
       
class AdminPdfUpload(APIView):
    def post(self, request):     
        class_selected = request.data.get('class_selected')
        subject_selected = request.data.get('subject_selected')
        pdf_file = request.FILES.get('pdf') 
        exam_id = request.data.get('exam_id')
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
                print("Creating Embeddings for pdf")
                pdf_extracted_text = extract_text_from_pdf(pdf_file_full_path)
                pdf_sentence,pdf_sentence_embeddings = get_paragraph_embedding(pdf_extracted_text)

                

            if question_image:
                print("Creating Embeddings for question")
                question_image_extracted_text = extract_questions_from_image(question_image_full_path)
                # Check the type of the extracted text
                print("Type of extracted text:", type(question_image_extracted_text))

                if isinstance(question_image_extracted_text, dict):
                    print("Extracted question dictionary:", question_image_extracted_text)
                    list_of_tuples = list(question_image_extracted_text.items())
                    print("List of tuples:", list_of_tuples)
                    question_sentence = " ".join([f"{key}: {value}" for key, value in list_of_tuples])
                    print("Combined question sentence:", question_sentence)
                    question_sentence, question_sentence_embeddings = get_paragraph_embedding(question_sentence)
                    response_data["question_image_extracted_text"] = question_image_extracted_text
                else:
                    print("The extracted text is not a dictionary.")
                    
            # print(pdf_file.name)

            pdfs_collection = get_collection("pdf_questions")
            try:
                if pdf_file and question_image:
                    pdfs_collection.insert_one({
                        "class_selected": class_selected,
                        "subject_selected": subject_selected,
                        "exam_id": exam_id,
                        # "pdf_file_name": pdf_file.name,
                        "pdf_file_path": pdf_file_full_path,
                        "pdf_extracted_text": pdf_extracted_text,
                        "pdf_sentence":pdf_sentence,
                        "pdf_sentence_embeddings":pdf_sentence_embeddings.tolist(),
                        "question_image_path": question_image_full_path,
                        "question_image_extracted_text": question_image_extracted_text,
                        "question_sentence":question_sentence,
                        "question_sentence_embeddings":question_sentence_embeddings.tolist()
                    })

            except Exception as e : 
                return Response({"message":"Error while inserting questoins in db"},status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({"message": "Files uploaded successfully.", **response_data}, status=200)

        except Exception as e:
            return Response({"message": f"An error occurred: {str(e)}"}, status=500)
        
class AdminPdfGetUpload(APIView):
    def get(self, request):
        try:
            pdfs_collection = get_collection("pdf_questions")
            print(pdfs_collection)
            return Response({"pdfs": "Success"}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"message": f"An error occurred: {str(e)}"}, status=500)


class UserUploadAnswer(APIView):
     # permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        if request.method == 'POST' and request.FILES['answer_image'] :
            answer_image = request.FILES['answer_image']
            answer_image_path = fs.save(answer_image.name, answer_image)
            answer_image_full_path = fs.path(answer_image_path)

            # ritu
            try:
                extracted_text = extract_text_from_pdf(answer_image_full_path)
                sentences, sentence_embeddings = get_paragraph_embedding(extracted_text)
                answers_embeddings_collection = get_collection("answers")
                answers_embeddings_collection.insert_one({
                    "answer_image_path": answer_image_full_path,
                    "extracted_text": extracted_text,
                    "embeddings": sentence_embeddings.tolist()
                })

                return  Response({'message': 'Answer Uploaded and Analyzed Sucessfully'}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"message": f"An error occurred while creating embeddings : {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
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

    return render(request, 'qa/upload.html')
    
    
class ClassListCreateAPI(APIView):

    def get(self, request):
        classes_collection = get_collection("classes")
        classes = list(classes_collection.find({}))
        for cls in classes:
            cls["_id"] = str(cls["_id"])  # Convert ObjectId to string
        return Response(classes, status=status.HTTP_200_OK)

    def post(self, request):
        data = request.data
        classes_collection = get_collection("classes")
        if classes_collection.find_one({"name": data["name"]}):
            return Response({"error": "Class already exists"}, status=400)
        classes_collection.insert_one(data)
        return Response({"message": "Class created successfully"}, status=status.HTTP_201_CREATED)


class SubjectListCreateAPI(APIView):
    
    def get(self, request, id=None):
        subjects_collection = get_collection("subjects")
        if id:
            subjects = list(subjects_collection.find({"associated_class_id": id}))
        else:
            subjects = list(subjects_collection.find({}))
        for subject in subjects:
            subject["_id"] = str(subject["_id"]) 
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
            roll_no = request.data.get('rollNo')
            exam_id = request.data.get('examId')
            class_id = request.data.get('classId')
            subject = request.data.get('subject')
            pdf_file = request.FILES.get('pdf')
            print(roll_no)
            if not roll_no: 
                return Response({"error": "Roll fields are required"}, status=status.HTTP_400_BAD_REQUEST)
            
            if not  exam_id: 
                return Response({"error": "Exam field are required "}, status=status.HTTP_400_BAD_REQUEST)
            
            if not class_id: 
                return Response({"error": "Class id is required  "}, status=status.HTTP_400_BAD_REQUEST)
            
            if  not subject: 
                return Response({"error": "Subject field is reqired"}, status=status.HTTP_400_BAD_REQUEST)
            
            if not pdf_file: 
                return Response({"error": "Pdf is Required"}, status=status.HTTP_400_BAD_REQUEST)
            
            fs = FileSystemStorage()
            pdf_file_path = fs.save(pdf_file.name, pdf_file)
            pdf_file_full_path = fs.path(pdf_file_path)

            # ritu
            extracted_text = extract_text_from_pdf(pdf_file_full_path)
            sentences, sentence_embeddings = get_paragraph_embedding(extracted_text)


            answers_collection = get_collection("answers")
            answers_collection.insert_one({
                "roll_no": roll_no,
                "exam_id": exam_id,
                "class_id": class_id,
                "subject": subject,
                "pdf_file_path": pdf_file_full_path,
                "extracted_text": extracted_text,
                "sentence_embeddings": sentence_embeddings.tolist(),
                "sentences":sentences
                
            })
        except Exception as e :
            return Response({"message":"Bad Request"} , status=status.HTTP_501_NOT_IMPLEMENTED)

        return Response({"message": "Answer uploaded successfully"}, status=status.HTTP_201_CREATED)


