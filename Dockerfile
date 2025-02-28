FROM python:3.10-bookworm 

WORKDIR /ocr_web_app_ml

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000" ]
