import openai
from pdf2image import convert_from_path
from django.conf import settings
import re
import os
from PyPDF2 import PdfReader


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
    openai.api_key = settings.OPENAI_API_KEY


    # Use the chat completion endpoint for the model
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini-2024-07-18",  
        messages=messages,
        max_tokens=150,
        temperature=0,
       
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
