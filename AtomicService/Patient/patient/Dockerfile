FROM python:3-slim
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY ./patient.py . 
EXPOSE 5001 
CMD [ "python", "./patient.py" ]