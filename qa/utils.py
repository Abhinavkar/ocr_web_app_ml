import openai
from pdf2image import convert_from_path
from django.conf import settings
import re
import os

openai.api_key = settings.OPENAI_API_KEY

def convert_pdf_to_images(pdf_path):
    images = convert_from_path(pdf_path)
    image_paths = []
    
    for i, image in enumerate(images):
        image_path = f"ocr_app/temp_image_{i + 1}.png"
        image.save(image_path, 'PNG')
        image_paths.append(image_path)
    
    return image_paths

def extract_text_from_images(image_paths):
    extracted_text = []

    for image_path in image_paths:
        with open(image_path, "rb") as image_file:
            response = openai.Image.create(
                image=image_file,
                model="vision-001"  
            )
            extracted_text.append(response['text'])
        os.remove(image_path)
    
    return extracted_text

def extract_answers_from_text(text):
    answers = []
    answer_pattern = r"Answer: (.*?)(?=Question|$)"  
    matches = re.findall(answer_pattern, text, re.DOTALL)
    for match in matches:
        answers.append(match.strip())
    
    return answers

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
