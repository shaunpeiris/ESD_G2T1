FROM python:3-slim
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt
RUN pip install pika 
COPY ./process.py .
COPY ./invokes.py .
COPY ./amqp_connection.py . 
CMD [ "python", "./process.py" ]