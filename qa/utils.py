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
