FROM python:3.9-slim
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY ./notification.py .
CMD ["python", "./notification.py", "--port", "5005"]