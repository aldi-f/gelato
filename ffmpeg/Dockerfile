FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    pkg-config \
    && apt-get build-dep -y ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
RUN git clone --branch test/5.1.4/main https://github.com/jc-kynesim/rpi-ffmpeg.git

WORKDIR /build/rpi-ffmpeg
RUN ./pi-util/conf_native.sh && \
    make -j$(nproc) -C out/*/install && \
    cp -r out/*/install/* /usr && \
    ./pi-util/clean_usr_libs.sh

RUN mkdir -p /dist && \
    cp -r out/*/install/* /dist/