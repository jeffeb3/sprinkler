FROM resin/rpi-raspbian:jessie
MAINTAINER Jeffeb3 <jeffeb3@gmail.com>

# Install dependencies
RUN apt-get update && apt-get install -y \
    git-core \
    build-essential \
    gcc \
    python \
    python-dev \
    python-pip \
    python-virtualenv \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

RUN pip install pyserial
RUN pip install bottle
RUN pip install paste
RUN pip install RPi.GPIO

RUN git clone https://github.com/jeffeb3/sprinkler /data

# Define working directory
WORKDIR /data
VOLUME /data

CMD ["python", "sprinklerApp.py"]
