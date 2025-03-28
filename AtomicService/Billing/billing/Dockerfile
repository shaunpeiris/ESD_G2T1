FROM python:3-slim
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY . .

# Set the Flask app to run on port 5004
CMD ["python", "./app.py", "--port", "5004"]
