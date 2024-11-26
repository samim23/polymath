FROM python:3.8-slim-buster

RUN apt-get update \
    && apt-get -y install rubberband-cli \
    libasound-dev portaudio19-dev \
    libportaudio2 libportaudiocpp0 git gcc \
    && rm -rf /var/lib/apt/lists/*

RUN pip install git+https://github.com/CPJKU/madmom.git@0551aa8

WORKDIR /polymath
COPY . .
RUN pip install -r ./requirements.txt

# fixes for some dependency conflicts
RUN pip uninstall -y soundfile
RUN pip install soundfile
RUN pip install soundfile==0.12.1
RUN pip install numpy==1.22.4
RUN pip uninstall -y essentia essentia-tensorflow
RUN pip install essentia-tensorflow
