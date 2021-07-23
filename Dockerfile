FROM python:3.7

WORKDIR /pipeline

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

RUN apt-get update ##[edited]
RUN apt-get install ffmpeg libsm6 libxext6  -y


COPY . /pipeline

