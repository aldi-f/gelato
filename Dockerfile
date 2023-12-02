FROM ubuntu:20.04

USER root

# Set timezone:
RUN ln -snf /usr/share/zoneinfo/$CONTAINER_TIMEZONE /etc/localtime && echo $CONTAINER_TIMEZONE > /etc/timezone


# install google chrome and ffmpeg
RUN echo "deb http://archive.ubuntu.com/ubuntu/ focal main restricted universe multiverse\n" > /etc/apt/sources.list \
  && echo "deb http://archive.ubuntu.com/ubuntu/ focal-updates main restricted universe multiverse\n" >> /etc/apt/sources.list \
  && echo "deb http://archive.ubuntu.com/ubuntu/ focal-security main restricted universe multiverse\n" >> /etc/apt/sources.list \
  && echo "deb http://archive.ubuntu.com/ubuntu/ focal-backports main restricted universe multiverse\n" >> /etc/apt/sources.list \
  && echo "deb http://archive.canonical.com/ubuntu focal partner\n" >> /etc/apt/sources.list 
RUN apt-get -y update
RUN apt-get install -y\
    # chromium\
    # unzip\
    tzdata\
    chromium-chromedriver\
    ffmpeg\
    python3-pip\
    && rm -rf /var/lib/apt/lists/*



RUN python3 --version
# # install chromedriver
# RUN echo "Geting ChromeDriver latest version from https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_" \
#     && CHROME_MAJOR_VERSION=$(google-chrome --version | sed -E "s/.* ([0-9]+)(\.[0-9]+){3}.*/\1/") \
#     && CHROME_DRIVER_VERSION=$(wget -qO- https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_${CHROME_MAJOR_VERSION} | sed 's/\r$//') \
#     && CHROME_DRIVER_URL="https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/$CHROME_DRIVER_VERSION/linux64/chromedriver-linux64.zip" \
#     && echo "Using ChromeDriver from: "$CHROME_DRIVER_URL \
#     && echo "Using ChromeDriver version: "$CHROME_DRIVER_VERSION \
#     && wget --no-verbose -O /tmp/chromedriver_linux64.zip $CHROME_DRIVER_URL \
#     && unzip /tmp/chromedriver_linux64.zip chromedriver-linux64/chromedriver -d /app/

COPY requirements.txt .

RUN python3 -m pip install  -r requirements.txt --user 

COPY ./app ./app

WORKDIR /app

CMD ["python3","./gelato.py"]
