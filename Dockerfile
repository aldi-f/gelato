FROM python:3.12-bookworm

RUN apt-get update && apt-get install -y wget xvfb libgtk-3-0 libx11-xcb1 libasound2

RUN wget https://github.com/jellyfin/jellyfin-ffmpeg/releases/download/v7.0.2-9/jellyfin-ffmpeg7_7.0.2-9-bookworm_amd64.deb -O /tmp/jellyfin-ffmpeg7_7.0.2-9-bookworm_amd64.deb && \
    apt-get install -y /tmp/jellyfin-ffmpeg7_7.0.2-9-bookworm_amd64.deb && \
    rm /tmp/jellyfin-ffmpeg7_7.0.2-9-bookworm_amd64.deb

ENV PATH="/usr/lib/jellyfin-ffmpeg:${PATH}"

COPY requirements.txt .

RUN python3 -m pip install -r requirements.txt --user --no-cache-dir

# Install camoufox
RUN python3 -m pip install camoufox[geoip] --user && \
    python3 -m camoufox fetch

COPY ./app /app

WORKDIR /app

CMD ["python3","-m", "gelato"]
