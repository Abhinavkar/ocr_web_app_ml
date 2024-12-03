from django.shortcuts import render
from .forms import DocumentForm, ImageForm
from django.http import JsonResponse
from .utils import extract_text_from_pdf, extract_text_from_image, ask_question
from .models import Document, Image
from django.core.files.storage import FileSystemStorage

# Your function for extracting PDF text and processing image logic should be in utils.py.

def home(request):
    return render(request, 'qa/home.html')

from django.shortcuts import render
from django.conf import settings
from .utils import process_uploaded_files
from django.core.files.storage import FileSystemStorage

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