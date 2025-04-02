FROM python:3-slim
WORKDIR /usr/src/app
COPY requirements.txt ./ ./invokes.py ./
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY ./doctormanagement.py .
CMD [ "python", "./doctormanagement.py" ]