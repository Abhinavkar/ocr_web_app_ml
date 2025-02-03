import PyPDF2
from together import Together
from dotenv import load_dotenv
import os
##########################################################################
import re
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import torch
from transformers import XLMRobertaTokenizer, XLMRobertaModel
from pdf2image import convert_from_path
import tempfile
import pdfplumber
import base64
from authentication.db_wrapper import get_collection
from PIL import Image 
from django.conf import settings
import cv2 
import pytesseract
from requests import Response
import together
import torch
from transformers import BertTokenizer, BertForSequenceClassification
from sentence_transformers import SentenceTransformer, util
import textstat

##########################################################################

# Load environment variables from .env file
load_dotenv()

# Function to extract text from PDFs
def extract_text_from_pdf(pdf_path):
    text = ""
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page in pdf_reader.pages:
            if page.extract_text():
                text += page.extract_text()
    return text

##########################################################################
def preprocess_image(image):
    """
    Preprocess the image for better OCR results.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    return binary
def encode_image_to_base64(image_path):
    """
    Encode an image file to a base64 string.
    """
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except FileNotFoundError:
        return None

def extract_text_from_image(image_path, prompt):
    """
    Extract text from an image using Together's Vision-Instruct-Turbo model.
    """
    print("Processing the image... Please wait.")

    base64_image = encode_image_to_base64(image_path)
    if not base64_image:
        return "Error: Image file not found."
    client = get_together_client()
    stream = client.chat.completions.create(
        model="meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo",
        messages=[
            {"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}]}
        ],
        stream=True,
    )

    extracted_text = ""
    for chunk in stream:
        if (chunk.choices and chunk.choices[0].delta.content):
            extracted_text += chunk.choices[0].delta.content

    return extracted_text.strip()



def convert_pdf_to_images(pdf_file_path, output_folder, image_format="jpeg"):
    """
    Convert each page of a PDF into an image and save it in the specified format.

    Args:
        pdf_file_path (str): Path to the PDF file.
        output_folder (str): Directory to save the output images.
        image_format (str): Image format to save ('png', 'jpg', 'jpeg').
        
    Returns:
        list: Paths to the generated image files.
    """
    # Validate the image format
    valid_formats = ["png", "jpg", "jpeg"]
    if image_format.lower() not in valid_formats:
        raise ValueError(f"Invalid image format: {image_format}. Supported formats are: {', '.join(valid_formats)}")
    
    # Ensure the output folder exists
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    
    # Convert PDF to images
    images = convert_from_path(pdf_file_path, dpi=300)
    image_paths = []
    
    # Save each page as an image
    for i, image in enumerate(images):
        image_path = os.path.join(output_folder, f"page_{i+1}.{image_format}")
        print(f"Processing image file: {image_path}")

        image.save(image_path, image_format.upper())  # Save in the specified format
        image_paths.append(image_path)
    print(f"PDF converted to images: {image_paths}")
    return image_paths



def extract_answers_from_image(image_path):
    """
    Extract answers from an image and index them.
    """
    ocr_prompt = "Analyze the given image to identify and extract all handwritten text. I want only the answer in the output. If there are multiple answers , index each distinct point sequentially."
    extracted_text = extract_text_from_image(image_path, ocr_prompt)
    answers = re.findall(r'\d+\.\s+(.*?)(?=\d+\.|$)', extracted_text, re.DOTALL)
    indexed_answers = {f"Answer {i+1}": answer.replace('\n', ' ').strip() for i, answer in enumerate(answers)}
    print(indexed_answers)
    return indexed_answers


##########################################################################

def get_together_client():
    api_key = os.getenv("TOGETHER_API_KEY")
    if not api_key:
        raise ValueError("API Key is missing from .env file.")
    client = Together(api_key=api_key)
    return client

def generate_response(chapter_text, questions_text):
    client = get_together_client()

    messages = [
        {"role": "user", "content": f"Chapter Content: {chapter_text}\nQuestions: {questions_text}"}
    ]

    # Get completion from Together AI
    completion = client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
        messages=messages,
    )
    print(messages)
    return completion.choices[0].message.content



######################################################################################
def extract_answers_from_pdf(pdf_file_path):
    """
    Extract answers from a multi-page PDF.
    """
    output_folder = os.path.join("answer_images", os.path.splitext(os.path.basename(pdf_file_path))[0])
    image_paths = convert_pdf_to_images(pdf_file_path, output_folder)
    
    user_answers = {}
    answer_counter = 1

    for image_path in image_paths:
        print(f"Processing image: {image_path}")
        extracted_answers = extract_answers_from_image(image_path)
        
        for key, value in extracted_answers.items():
            user_answers[f"Answer {answer_counter}"] = value
            answer_counter += 1
            print(f"Answer {user_answers}")
  
    return user_answers



def evaluate_answer(user_answer, model_answer):
#    ask lllama to compare and tell the score 
    api_key = os.getenv("TOGETHER_API_KEY")
    client = get_together_client()
    messages = [
        {"role": "user", "content": f"User Answer: {user_answer}\n Model Answer: {model_answer} Evaluate the answer according to the model answer and give us score to each answer out of 100 on the basis of factual correctness, relevance, and completeness. Scoring format is Answer 1: 80, Answer 2: 90, etc."}
    ]
    completion = client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
        messages=messages,
    )
    print(messages)
    return completion.choices[0].message.content


# #######################################################################################















































# def extract_text_from_pdf(file_path):
#     """Extract text from a PDF file."""
#     try:
#         reader = PdfReader(file_path)
#         text = "\n".join(page.extract_text() for page in reader.pages)
#         return text
#     except Exception as e:
#         raise ValueError(f"Error reading PDF file: {e}")



# def split_questions_from_text(pdf_path):
#     """Extract questions from a PDF file."""
#     with open(pdf_path, 'rb') as file:
#         pdf_reader = PdfReader(file)
#         first_page = pdf_reader.pages[0]
#         text = first_page.extract_text()
#         questions = re.findall(r'\d*\.*\s*([^?]+\?*)', text)
#         cleaned_questions = [
#             re.sub(r'\s+', ' ', q).strip()
#             for q in questions
#             if len(q.strip()) > 3
#         ]
#         return cleaned_questions
    
    
    
# def get_answer(question, context):
#     """Get the most relevant answer for a question from a context using OpenAI API."""
#     # Define the system message and user query as chat messages
#     messages = [
#         {"role": "system", "content": "You are a helpful assistant."},
#         {"role": "user", "content": f"Context: {context}\n\nQuestion: {question}"}
#     ]
#     openai.api_key = settings.OPENAI_API_KEY


#     # Use the chat completion endpoint for the model
#     response = openai.ChatCompletion.create(
#         model="gpt-4o-mini-2024-07-18",  
#         messages=messages,
#         max_tokens=150,
#         temperature=0,
       
#     )

#     answer = response['choices'][0]['message']['content'].strip()
#     return answer



# def display_results(question, context):
#     """Display search results for an individual question with answers."""
#     print(f"\n[QUESTION] {question}")
#     print(f"\n[Context]:")
#     print(f"{context[:500]}...")  # Display a snippet of the context (first 500 characters)

#     answer = get_answer(question, context)
#     print(f"Answer: {answer}")
#     print(f"{'-'*80}")
