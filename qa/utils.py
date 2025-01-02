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


model = SentenceTransformer('BAAI/bge-large-en-v1.5')

api_key = "353a19336b7e42fe5e8f4645074618f8a7a4e0eefcee7a5047f6d7c86a2b6e1f"
client = Together(api_key=api_key)


def extract_text_from_pdf(pdf_path):
    """
    Extract text from a PDF file using pdfplumber.
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = "".join(page.extract_text() or "" for page in pdf.pages)
        return full_text
    except Exception as e:
        return f"Error extracting text from PDF: {str(e)}"


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


def extract_questions_from_image(image_path):
    """
    Extract questions from an image and index them.
    """
    ocr_prompt = "Analyze the given image to identify and extract all handwritten text. I want only the questions in the output. If there are multiple questions, index each distinct point sequentially."
    extracted_text = extract_text_from_image(image_path, ocr_prompt)

    

    # Use regex to find numbered questions
    questions = re.findall(r'\d+\.\s+(.*?)(?=\d+\.\s|$)', extracted_text, re.DOTALL)
    indexed_questions = {f"Question {i + 1}": question.replace('\n', ' ').strip() for i, question in enumerate(questions)}
    print(indexed_questions)

    return indexed_questions


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


def remove_auxiliary_words(text):
    text  = text.split('')
    text  = text.lower()
    auxiliaryVerbs = [  "am", "is", "are", "was", "were", "be", "being", "been",  "have", "has", "had",  "do", "does", "did",  "shall", "should", "will", "would", "can", "could", "may", "might", "must", "ought", "need", "dare", "used to"]


def get_paragraph_embedding(paragraph):
    """
    Generate sentence embeddings for a given paragraph.
    """
    sentences = paragraph.split('.')
    sentence_embeddings = model.encode(sentences, convert_to_tensor=True)
    return sentences, sentence_embeddings

def ask_question(paragraph, user_question, user_answer=None):
    """Find the best matching sentence for the user's question and compare their answer."""
    user_question_embedding = model.encode(user_question, convert_to_tensor=True)
    sentences, sentence_embeddings = get_paragraph_embedding(paragraph) 

    best_match_score = 0
    best_match_sentence = ""
    for i, sentence_embedding in enumerate(sentence_embeddings):
        similarity_score = util.cos_sim(user_question_embedding, sentence_embedding).item() * 100
        if similarity_score > best_match_score:
            best_match_score = similarity_score
            best_match_sentence = sentences[i]

    print(f"Best matching sentence: {best_match_sentence.strip()}")
    print(f"Similarity score (question vs. sentence): {best_match_score:.2f}%")

    answer_similarity_score = 0
    answer_relevance = "No user answer provided for comparison."
    if user_answer:
        reference_embedding = model.encode(best_match_sentence, convert_to_tensor=True)
        user_answer_embedding = model.encode(user_answer, convert_to_tensor=True)
        answer_similarity_score = util.cos_sim(user_answer_embedding, reference_embedding).item() * 100

        print(f"Similarity score (user answer vs. reference): {answer_similarity_score:.2f}%")
        if answer_similarity_score > 65:
            answer_relevance = "Your answer is highly relevant!"
        else:
            answer_relevance = "Your answer does not closely match the reference answer."
        # print(ask_question(paragraph,user_question,user_answer))


    return best_match_sentence.strip(), best_match_score, answer_similarity_score, answer_relevance

def process_uploaded_files(pdf_file_path, question_image_path, answer_image_path):
    """
    Process uploaded files (PDF and images) and return results for questions and answers.
    """
    paragraph = extract_text_from_pdf(pdf_file_path)
    questions = extract_questions_from_image(question_image_path)
    answers = extract_answers_from_image(answer_image_path)
    results = []
    for question_label, user_question in questions.items():
        answer_label = question_label.replace("Question", "Answer")
        user_answer = answers.get(answer_label, "")
        result = ask_question(paragraph, user_question, user_answer)
        results.append({'question_label': question_label, 'result': result})
        

    return results

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
def extract_text_from_image1(image_path):
    """
    Extract text from a single image using Tesseract OCR.
    """
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Error reading image: {image_path}")
    preprocessed_image = preprocess_image(image)
    return pytesseract.image_to_string(preprocessed_image)
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
  
    return user_answers


def get_stored_result(roll_no, exam_id, class_id, subject):
    """
    Fetch stored result from the database with proper validation.

    Parameters:
        roll_no (str): The roll number of the student.
        exam_id (str): The ID of the exam.
        class_id (str): The ID of the class.
        subject (str): The subject name or ID.

    Returns:
        str or None: The stored result if found, otherwise None.
    """
    # Validate inputs
    if not roll_no:
        raise ValueError("Roll number must be provided.")
    if not exam_id:
        raise ValueError("Exam ID must be provided.")
    if not class_id:
        raise ValueError("Class ID must be provided.")
    if not subject:
        raise ValueError("Subject must be provided.")

    # Perform database query
    try:
        answers_db_collection = get_collection("answers_db")
        result = answers_db_collection.find_one({
            "roll_no": roll_no,
            "exam_id": exam_id,
            "class_id": class_id,
            "subject": subject
        })
        if result:
            # Ensure 'result' key exists in the document
            if 'result' in result:
                return result['result']
            else:
                print("Warning: 'result' key is missing in the retrieved document.")
                return None
        else:
            # No result found in the database
            return None

    except Exception as e:
        # Handle potential database or other errors
        print(f"An error occurred while fetching the stored result: {e}")
        return None
