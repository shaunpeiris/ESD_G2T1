FROM python:3.9-slim

WORKDIR /Pharmacy

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5004

CMD ["python", "pharmacy.py"]
