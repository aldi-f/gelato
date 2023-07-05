FROM python:3.10-buster

COPY requirements.txt .

USER root

RUN apt-get update && \
    apt-get install ffmpeg -y

RUN python3 -m pip install  -r requirements.txt --user 

COPY ./app ./app

WORKDIR /app

CMD ["python3","./gelato.py"]
