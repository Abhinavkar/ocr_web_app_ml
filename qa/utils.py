import PyPDF2
from together import Together
from dotenv import load_dotenv
import os
##########################################################################
import re

import numpy as np

from pdf2image import convert_from_path
import tempfile
import base64
from authentication.db_wrapper import get_collection
from PIL import Image 
from django.conf import settings
# import cv2 
import pytesseract


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
# def preprocess_image(image):
    # """
    # Preprocess the image for better OCR results.
    # """
    # gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    # return binary
def encode_image_to_base64(image_path):
    """
    Encode an image file to a base64 string.
    """
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except FileNotFoundError:
        return None

# def extract_text_from_image(image_path, prompt):
#     """
#     Extract text from an image using Together's Vision-Instruct-Turbo model.
#     """
#     print("Processing the image... Please wait.")

#     base64_image = encode_image_to_base64(image_path)
#     if not base64_image:
#         return "Error: Image file not found."
#     client = get_together_client()
#     stream = client.chat.completions.create(
#         model="meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo",
#         messages=[
#             {"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}]}
#         ],
#         stream=True,
#     )

#     extracted_text = ""
#     for chunk in stream:
#         if (chunk.choices and chunk.choices[0].delta.content):
#             extracted_text += chunk.choices[0].delta.content

#     return extracted_text.strip()



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

# def preprocess_image(image):
    # """
    # Preprocess the image for better OCR results.
    # """
    # gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    # return binary
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
        model="meta-llama/Llama-3.2-90B-Vision-Instruct-Turbo",
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
    {
        "role": "user",
        "content": (
            f"User Answer: {user_answer}\n"
            f"Model Answer: {model_answer}\n"
            "You are evaluating user responses in a chatbot interaction. Compare the user answer with the model's answer with respect to questions provided using the following criteria:\n"
            "Relevance: Does the user response directly address the question provided?\n"
            "Clarity: Is the user's answer easy to understand and free from ambiguity?\n"
            "Correctness: Does the user's logic or explanation align with the correct concepts or facts?\n"
            "Factual Accuracy: Are the details provided by the user factually correct?\n"
            "Assign a score that is mention in the question like (5 marks or 3 marks )accordingly based on how well the user response meets these criteria. If points are deducted, explain clearly and concisely which criteria were not met and why.\n"
            "Ensure the output strictly follows this JSON format:\n"
            "The remarks must be actionable and specific, avoiding vague or generic feedback.\n"
            "Ensure the tone remains neutral and constructive.\n"
            '{\n'
            '"question_1": {\n'
            '"question": "Insert the provided question here",\n'
            '"answer_1": "Insert the user\'s response here",\n'
            '"model_answer": "Insert the chatbot\'s correct answer here",\n'
            '"Evaluator Remark": "Explain why marks were deducted — specify issues with relevance, clarity, correctness, or factual accuracy",\n'
            '"score": "Insert a score according to the mark given in question out of that score and show only the obtained mark"\n'
            '}\n'
            '}'
        )
    }
]
    completion = client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
        messages=messages,
    )
    print(messages)
    return completion.choices[0].message.content


# ############################################################




