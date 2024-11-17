FROM python:3.12-slim-bookworm

RUN get http://apt.undo.it:7241/apt.undo.it.asc -O /etc/apt/trusted.gpg.d/apt.undo.it.asc
RUN echo "deb http://apt.undo.it:7241/debian bookworm main" | sudo tee /etc/apt/sources.list.d/apt.undo.it.list

RUN apt-get -y update
RUN apt-get install -y\
    wget\
    ffmpeg-v4l2request\
    python3-pip

WORKDIR /tmp

COPY requirements.txt .

RUN python3 -m pip install  -r requirements.txt --user 

COPY ./app /app

WORKDIR /app

CMD ["python3","-m", "gelato"]
