FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive
ENV GECKO_VERSION=v0.33.0

RUN apt-get -y update
RUN apt-get install -y\
    wget\
    ffmpeg\
    python3-pip

WORKDIR /tmp
RUN wget https://github.com/mozilla/geckodriver/releases/download/${GECKO_VERSION}/geckodriver-${GECKO_VERSION}-linux-aarch64.tar.gz
RUN tar -xzf geckodriver-${GECKO_VERSION}-linux-aarch64.tar.gz
RUN chmod +x geckodriver 
RUN mv geckodriver /usr/local/bin/

RUN apt-get install -y\
    firefox\
    && rm -rf /var/lib/apt/lists/*

RUN export MOZ_HEADLESS=1
ENV display=:0

COPY requirements.txt .

RUN python3 -m pip install  -r requirements.txt --user 

COPY ./app /app

WORKDIR /app

CMD ["python3","./gelato.py"]
