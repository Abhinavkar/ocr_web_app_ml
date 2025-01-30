from sentence_transformers import SentenceTransformer, util
from together import Together
import base64
import pdfplumber
import os
import re
from django.conf import settings
# Use relative import if authentication is part of the same project
from authentication.db_wrapper import get_collection
from authentication.db_wrapper import get_collection
from pdf2image import convert_from_path
import cv2 
import pytesseract
from PIL import Image 
import tempfile
from rest_framework.response import Response
from rest_framework import status


from PyPDF2 import PdfReader
import openai


def extract_text_from_pdf(file_path):
    """Extract text from a PDF file."""
    try:
        reader = PdfReader(file_path)
        text = "\n".join(page.extract_text() for page in reader.pages)
        return text
    except Exception as e:
        raise ValueError(f"Error reading PDF file: {e}")



def split_questions_from_text(pdf_path):
    """Extract questions from a PDF file."""
    with open(pdf_path, 'rb') as file:
        pdf_reader = PdfReader(file)
        first_page = pdf_reader.pages[0]
        text = first_page.extract_text()
        questions = re.findall(r'\d*\.*\s*([^?]+\?*)', text)
        cleaned_questions = [
            re.sub(r'\s+', ' ', q).strip()
            for q in questions
            if len(q.strip()) > 3
        ]
        return cleaned_questions
    
    
    
def get_answer(question, context):
    """Get the most relevant answer for a question from a context using OpenAI API."""
    # Define the system message and user query as chat messages
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": f"Context: {context}\n\nQuestion: {question}"}
    ]

    # Use the chat completion endpoint for the model
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini-2024-07-18",  # You can use gpt-4 or gpt-3.5-turbo if needed
        messages=messages,
        max_tokens=150,
        temperature=0
    )

    answer = response['choices'][0]['message']['content'].strip()
    return answer



def display_results(question, context):
    """Display search results for an individual question with answers."""
    print(f"\n[QUESTION] {question}")
    print(f"\n[Context]:")
    print(f"{context[:500]}...")  # Display a snippet of the context (first 500 characters)

    answer = get_answer(question, context)
    print(f"Answer: {answer}")
    print(f"{'-'*80}")
