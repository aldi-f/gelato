FROM python:3.12-slim-bullseye

RUN apt-get -y update
RUN apt-get install -y\
    wget\
    ffmpeg\
    python3-pip

WORKDIR /tmp

COPY requirements.txt .

RUN python3 -m pip install  -r requirements.txt --user 

COPY ./app /app

WORKDIR /app

CMD ["python3","-m", "gelato"]
