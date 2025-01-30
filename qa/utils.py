import PyPDF2
from together import Together
from dotenv import load_dotenv
import os

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
