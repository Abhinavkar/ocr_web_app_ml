from sentence_transformers import SentenceTransformer, util
from together import Together
import base64
import pdfplumber
import os
import re
from django.conf import settings

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
        if chunk.choices and chunk.choices[0].delta.content:
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
    # print(indexed_questions)

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

    return best_match_sentence.strip(), best_match_score, answer_similarity_score, answer_relevance

def process_uploaded_files(pdf_file_path, question_image_path, answer_image_path):
    """
    Process uploaded files (PDF and images) and return results for questions and answers.
    """
    paragraph = extract_text_from_pdf(pdf_file_path)
    questions = extract_questions_from_image(question_image_path)
    print(questions)
    answers = extract_answers_from_image(answer_image_path)
    print(answers)
    results = []
    for question_label, user_question in questions.items():
        answer_label = question_label.replace("Question", "Answer")
        user_answer = answers.get(answer_label, "")
        result = ask_question(paragraph, user_question, user_answer)
        results.append({'question_label': question_label, 'result': result})

    return results
