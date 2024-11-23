FROM python:3.9-slim

WORKDIR /app

RUN mkdir /logs

COPY app/requirements.txt . 

RUN pip install -r requirements.txt

COPY app/main.py .

CMD ["python", "main.py"]
