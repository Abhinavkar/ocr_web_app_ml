from sentence_transformers import SentenceTransformer, util
from together import Together
import base64
import pdfplumber
import os
from django.conf import settings 
model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

api_key = "353a19336b7e42fe5e8f4645074618f8a7a4e0eefcee7a5047f6d7c86a2b6e1f"
client = Together(api_key=api_key)

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                full_text += page.extract_text()
        return full_text
    except Exception as e:
        return f"Error extracting text from PDF: {str(e)}"

def get_paragraph_embedding(paragraph):
    """Encode the paragraph into embeddings for sentence comparison."""
    sentences = paragraph.split('.')
    sentence_embeddings = model.encode(sentences, convert_to_tensor=True)
    return sentences, sentence_embeddings

def extract_text_from_image(image_path):
    """Extract text from an image using OCR."""
    print("Processing the image... Please wait.")

    def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    base64_image = encode_image(image_path)

    ocr_prompt = "You are an expert in handwriting recognition. Carefully read and extract all the text from the attached image, ensuring the transcription is as accurate as possible."

    stream = client.chat.completions.create(
        model="meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": ocr_prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                        },
                    },
                ],
            }
        ],
        stream=True,
    )

    extracted_text = ""
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            extracted_text += chunk.choices[0].delta.content
    return extracted_text.strip()


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
        if answer_similarity_score > 70:
            answer_relevance = "Your answer is highly relevant!"
        else:
            answer_relevance = "Your answer does not closely match the reference answer."

    return best_match_sentence.strip(), best_match_score, answer_similarity_score, answer_relevance

def process_uploaded_files(pdf_file_path, question_image_path, answer_image_path):
    """
    Process the uploaded files: Extract text from PDF and images and return the result.
    """
    paragraph = extract_text_from_pdf(pdf_file_path)

    user_question = extract_text_from_image(question_image_path)
    user_answer = extract_text_from_image(answer_image_path)

    best_match_sentence, best_match_score, answer_similarity_score, answer_relevance = ask_question(paragraph, user_question, user_answer)

    result = {
        'best_match_sentence': best_match_sentence,
        'best_match_score': best_match_score,
        'answer_similarity_score': answer_similarity_score,
        'answer_relevance': answer_relevance
    }

    return result