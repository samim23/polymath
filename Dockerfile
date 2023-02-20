FROM python:3.10-bullseye

RUN apt update
RUN apt install -y make automake gcc g++ python3-dev gfortran build-essential wget libsndfile1 ffmpeg

RUN pip install --upgrade pip

COPY . /polymath
WORKDIR /polymath

RUN pip install -r requirements.txt

RUN mkdir -p input processed separated library

