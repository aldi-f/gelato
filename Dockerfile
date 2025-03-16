FROM python:3.12-bookworm

RUN apt-get update && apt-get install -y wget 

RUN wget https://github.com/jellyfin/jellyfin-ffmpeg/releases/download/v7.0.2-9/jellyfin-ffmpeg7_7.0.2-9-bookworm_amd64.deb -O /tmp/jellyfin-ffmpeg7_7.0.2-9-bookworm_amd64.deb && \
    apt-get install -y /tmp/jellyfin-ffmpeg7_7.0.2-9-bookworm_amd64.deb && \
    rm /tmp/jellyfin-ffmpeg7_7.0.2-9-bookworm_amd64.deb && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ENV PATH="/usr/lib/jellyfin-ffmpeg:${PATH}"

COPY requirements.txt .

RUN python3 -m pip install  -r requirements.txt --user

COPY ./app /app

WORKDIR /app

CMD ["python3","-m", "gelato"]
