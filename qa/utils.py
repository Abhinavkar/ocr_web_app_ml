import PyPDF2
from together import Together
from dotenv import load_dotenv
import os
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
from rest_framework import status
from PIL import Image 
from django.conf import settings
import cv2 
import pytesseract
from requests import Response

# Load XLM-RoBERTa tokenizer and model
tokenizer = XLMRobertaTokenizer.from_pretrained('xlm-roberta-base')
model = XLMRobertaModel.from_pretrained('xlm-roberta-base')
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
        model="meta-llama/Llama-3.2-3B-Instruct-Turbo",
        messages=messages,
    )
    print(messages)
    return completion.choices[0].message.content

def extract_questions_from_image(image_path):
    """
    Extract questions from an image and index them.
    """
    ocr_prompt = "Analyze the given image to identify and extract all printed text. I want only the questions in the output. If there are multiple questions, index each distinct point sequentially."
    extracted_text = extract_text_from_image(image_path, ocr_prompt)

    # Use regex to find numbered questions
    questions = re.findall(r'\d+\.\s+(.*?)(?=\d+\.\s|$)', extracted_text, re.DOTALL)
    indexed_questions = {f"Question {i + 1}": question.replace('\n', ' ').strip() for i, question in enumerate(questions)}
    print(indexed_questions)

    return indexed_questions
def extract_questions_from_images(image_paths):
    """
    Extract questions from a list of images.
    """
    questions = {}
    question_counter = 1  # Initialize question counter for sequential numbering

    for image_path in image_paths:
        print(f"Processing image: {image_path}")
        extracted_questions = extract_questions_from_image(image_path)
        
        # Update the question keys to ensure sequential numbering
        for key, value in extracted_questions.items():
            questions[f"Question {question_counter}"] = value
            question_counter += 1
    
    return questions
def extract_text_from_PDF(pdf_path):
    """
    Extract text from a PDF file using pdfplumber.
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = "".join(page.extract_text() or "" for page in pdf.pages)
        return full_text
    except Exception as e:
        return f"Error extracting text from PDF: {str(e)}"

def extract_text_from_scanned_pdf(pdf_path):
    """
    Extract text from scanned PDF using Tesseract OCR.
    """
    try:
        images = convert_from_path(pdf_path, dpi=300)
        question_text = ""

        for image in images:
            # Save image temporarily to use for OCR
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_image:
                image.save(temp_image.name)
                with open(temp_image.name, "rb") as img_file:
                    image_base64 = base64.b64encode(img_file.read()).decode("utf-8")

                # Perform OCR using Tesseract
                ocr_text = pytesseract.image_to_string(Image.open(temp_image.name))
                question_text += ocr_text

            # Optionally, clean up temporary files
            os.remove(temp_image.name)
     
        return question_text.strip()

    except Exception as e:
        raise Exception(f"Error extracting text from scanned PDF: {str(e)}")
    
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
def extract_questions_from_pdf(pdf_file_path):
    """
    Extract questions from a multi-page PDF and index them.
    """
    try:
        # Step 1: Define output folder for PDF-to-image conversion
        output_folder = os.path.join(
            settings.MEDIA_ROOT,
            "pdf_images",
            os.path.splitext(os.path.basename(pdf_file_path))[0]
        )
        
        # Step 2: Convert PDF to images
        image_paths = convert_pdf_to_images(pdf_file_path, output_folder)
        if not image_paths:
            raise ValueError("PDF conversion to images failed or returned no images.")

        # Step 3: Initialize a dictionary to store extracted questions
        extracted_questions = {}
        
        # Step 4: Process each image and extract questions
        for image_path in image_paths:
            print(f"Processing image: {image_path}")
            
            # Extract questions from the image
            questions = extract_questions_from_image(image_path)
            
            if not isinstance(questions, dict):
                print(f"Invalid data format for image {image_path}: {questions}")
                continue  # Skip to the next image
            
            # Add extracted questions to the dictionary
            extracted_questions.update(questions)

        # Step 5: Handle cases where no questions were found
        if not extracted_questions:
            raise ValueError("No valid questions found in the PDF.")
        
        print("Extracted Questions:", extracted_questions)
        return extracted_questions
    except Exception as e:
        print(f"Error extracting questions from images: {e}")
        # return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
# def extract_answers_from_pdf(pdf_file_path):
#     """
#     Extract answers from a multi-page PDF.
#     """
#     try:
#         output_folder = os.path.join("answer_images", os.path.splitext(os.path.basename(pdf_file_path))[0])
#         image_paths = convert_pdf_to_images(pdf_file_path, output_folder)
        
#         user_answers = {}
#         answer_counter = 1  # Initialize answer counter for sequential numbering

#         for image_path in image_paths:
#             print(f"Processing image: {image_path}")
#             extracted_answers = extract_answers_from_image(image_path)
            
#             # Update the answer keys to ensure sequential numbering
#             for key, value in extracted_answers.items():
#                 user_answers[f"Answer {answer_counter}"] = value
#                 answer_counter += 1
#         questions = extract_questions_from_image(image_paths)
#         return questions, user_answers
#     except Exception as e:
#         return Response({"error": f"Error extracting answers from PDF: {str(e)}"}, 
#                     status=status.HTTP_500_INTERNAL_SERVER_ERROR)
  
    # return user_answers

def extract_answers_from_pdf(pdf_file_path):
    """
    Extract answers from a multi-page PDF.
    """
    output_folder = os.path.join("answer_images", os.path.splitext(os.path.basename(pdf_file_path))[0])
    image_paths = convert_pdf_to_images(pdf_file_path, output_folder)
    
    user_answers = {}
    answer_counter = 1  # Initialize answer counter for sequential numbering

    for image_path in image_paths:
        print(f"Processing image: {image_path}")
        extracted_answers = extract_answers_from_image(image_path)
        
        # Update the answer keys to ensure sequential numbering
        for key, value in extracted_answers.items():
            user_answers[f"Answer {answer_counter}"] = value
            answer_counter += 1
  
    # Convert the dictionary values to a single string
    answers_text = "\n".join(user_answers.values())
    questions_text = ""  # Assuming questions_text is empty or obtained elsewhere

    questions, answers = parse_questions_and_answers(questions_text, answers_text)
    return questions, answers

def parse_questions_and_answers(questions_text, answers_text):
    questions = []
    answers = []

    try:
        if not questions_text.strip():
            raise ValueError("Extracted questions text is empty.")
        if not answers_text.strip():
            raise ValueError("Extracted answers text is empty.")

        question_pattern = re.compile(r"(\d+\.)(.*?)(?=\d+\.|\Z)", re.DOTALL | re.MULTILINE)
        question_matches = question_pattern.findall(questions_text)
        questions = [match[1].strip() for match in question_matches]

        answer_pattern = re.compile(r"(\d+\.)(.*?)(?=\d+\.|\Z)", re.DOTALL | re.MULTILINE)
        answer_matches = answer_pattern.findall(answers_text)
        answers = [match[1].strip() for match in answer_matches]

    except Exception as e:
        print(f"Error while parsing questions and answers: {e}")

    print(f"Questions: {questions}")
    print(f"Answers: {answers}")

    return questions, answers


def generate_xlmr_embeddings(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
    embeddings = outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
    return embeddings

def compute_xlmr_similarity(user_answer, model_generated_answer):
    user_embedding = generate_xlmr_embeddings(user_answer)
    model_embedding = generate_xlmr_embeddings(model_generated_answer)
    # similarity = cosine_similarity([user_embedding], [model_embedding])[0][0]
    similarity = cosine_similarity(user_embedding.reshape(1, -1), model_embedding.reshape(1, -1))[0][0]

    return similarity * 100  


def evaluate_answers(user_answer, model_generated_answer):
    xlmr_score = compute_xlmr_similarity(user_answer, model_generated_answer)
    factual_score = compute_factual_accuracy(user_answer, model_generated_answer)
    clarity_score = compute_clarity_and_length(user_answer)
    final_score = (xlmr_score * 0.7) + (factual_score * 0.2) + (clarity_score * 0.1)
    return final_score


def compute_factual_accuracy(user_answer, model_generated_answer):
    # Extract key terms or phrases from the model-generated answer
    key_terms = set(model_generated_answer.lower().split())
    user_terms = set(user_answer.lower().split())
    overlap = key_terms.intersection(user_terms)
    factual_score = (len(overlap) / len(key_terms)) * 100 if key_terms else 0
    return factual_score

def compute_clarity_and_length(user_answer):
    token_count = len(tokenizer.encode(user_answer))
    if token_count < 50:
        clarity_score = 50 
    elif token_count > 150:
        clarity_score = 50  
    else:
        clarity_score = 100
    return clarity_score









































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
