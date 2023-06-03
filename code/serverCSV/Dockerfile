FROM gcr.io/google_appengine/python:latest

WORKDIR /app
ADD . /app
RUN pip3 install -r requirements.txt
ENTRYPOINT ["python3", "server.py"]