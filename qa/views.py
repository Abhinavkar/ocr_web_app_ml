from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.decorators import login_required

# Your function for extracting PDF text and processing image logic should be in utils.py.
\
from .utils import process_uploaded_files
from django.core.files.storage import FileSystemStorage

@login_required
def home(request):
    return render(request, 'qa/home.html')

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


# def upload_files(request):
#     if request.method == 'POST':
#         # Check if all files are provided
#         if not all(field in request.FILES for field in ['pdf', 'question_image', 'answer_image']):
#             return render(request, 'qa/upload.html', {'error': "Please upload all required files (PDF, question image, and answer image)."})

#         try:
#             # Save uploaded files using FileSystemStorage
#             fs = FileSystemStorage()

#             pdf_file = request.FILES['pdf']
#             question_image = request.FILES['question_image']
#             answer_image = request.FILES['answer_image']

#             pdf_file_path = fs.save(pdf_file.name, pdf_file)
#             question_image_path = fs.save(question_image.name, question_image)
#             answer_image_path = fs.save(answer_image.name, answer_image)

#             pdf_file_full_path = fs.path(pdf_file_path)
#             question_image_full_path = fs.path(question_image_path)
#             answer_image_full_path = fs.path(answer_image_path)

#             # Process files and extract questions/answers
#             result = process_uploaded_files(pdf_file_full_path, question_image_full_path, answer_image_full_path)

#             # If there is an error in processing
#             if "error" in result:
#                 return render(request, 'qa/upload.html', {'error': result['error']})

#             # Render result page
#             return render(request, 'qa/result.html', {'result': result})

#         except Exception as e:
#             # Log and handle unexpected errors
#             print(f"Error during file upload: {e}")
#             return render(request, 'qa/upload.html', {'error': "An unexpected error occurred. Please try again."})

#     return render(request, 'qa/upload.html')