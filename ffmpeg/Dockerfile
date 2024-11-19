FROM debian:bookworm-slim

SHELL ["/bin/bash", "-c"]

RUN echo "deb-src http://deb.debian.org/debian bookworm main" >> /etc/apt/sources.list && \
    echo "deb-src http://security.debian.org/debian-security bookworm-security main" >> /etc/apt/sources.list && \
    echo "deb-src http://deb.debian.org/debian bookworm-updates main" >> /etc/apt/sources.list


RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    pkg-config \
    && apt-get build-dep -y ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
RUN git clone --branch test/5.1.4/main https://github.com/jc-kynesim/rpi-ffmpeg.git

WORKDIR /build/rpi-ffmpeg
RUN ./pi-util/conf_native.sh
RUN make -j$(nproc) -C out/arm64--5.1.4-shared-rel install

RUN mkdir -p /dist && \
    cp -r out/*/install/* /dist/
