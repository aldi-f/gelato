FROM python:3.12-slim-bookworm

RUN apt -y update && apt install -y wget
    
RUN wget http://apt.undo.it:7241/apt.undo.it.asc -O /etc/apt/trusted.gpg.d/apt.undo.it.asc
RUN echo "deb http://apt.undo.it:7241/debian bookworm main" | tee /etc/apt/sources.list.d/apt.undo.it.list

RUN apt -y update
RUN apt install -y\
    ffmpeg-v4l2request\
    python3-pip

WORKDIR /tmp

COPY requirements.txt .

RUN python3 -m pip install  -r requirements.txt --user 

COPY ./app /app

WORKDIR /app

CMD ["python3","-m", "gelato"]
