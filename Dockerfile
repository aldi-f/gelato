FROM python:3.12-bookworm

RUN apt -y update && apt install -y python3-pip ffmpeg

COPY requirements.txt .

RUN python3 -m pip install  -r requirements.txt --user 

COPY ./app /app

WORKDIR /app

CMD ["python3","-m", "gelato"]
