FROM python:3.12-slim-bookworm

ARG ARCH=arm64
ARG FFMPEG_VERSION=7.0.2-7


RUN apt -y update && apt install -y wget
RUN wget \
    https://github.com/jellyfin/jellyfin-ffmpeg/releases/download/v${FFMPEG_VERSION}/jellyfin-ffmpeg7_${FFMPEG_VERSION}-bookworm_${ARCH}.deb \
    && dpkg -i jellyfin-ffmpeg7_${FFMPEG_VERSION}-bookworm_${ARCH}.deb

RUN apt install -y python3-pip

WORKDIR /tmp

COPY requirements.txt .

RUN python3 -m pip install  -r requirements.txt --user 

COPY ./app /app

WORKDIR /app

CMD ["python3","-m", "gelato"]
