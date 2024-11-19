FROM python:3.12-slim-bookworm

RUN apt -y update && apt install -y python3-pip

COPY requirements.txt .

RUN python3 -m pip install  -r requirements.txt --user 

COPY ./app /app

FROM gelato-ffmpeg:latest as ffmpeg-builder

COPY --from=builder /dist/ /usr/local/ffmpeg/
ENV LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:/usr/local/ffmpeg/lib:/usr/local/ffmpeg/lib64:/usr/local/ffmpeg/lib/aarch64-linux-gnu"

WORKDIR /app

CMD ["python3","-m", "gelato"]
