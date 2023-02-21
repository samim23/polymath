
# Polymath

Polymath uses machine learning to convert any music library (*e.g from Hard-Drive or YouTube*) into a music production sample-library. The tool automatically separates songs into stems (*beats, bass, etc.*), quantizes them to the same tempo and beat-grid (*e.g. 120bpm*), analyzes musical structure (*e.g. verse, chorus, etc.*), key (*e.g C4, E3, etc.*) and other infos (*timbre, loudness, etc.*), and converts audio to midi. The result is a searchable sample library that streamlines the workflow for music producers, DJs, and ML audio developers.

<p align="center"><img alt="Polymath" src="https://samim.io/static/upload/illustration3.688a510b-bocuz8wh.png" /></p>

## Use-cases
Polymath makes it effortless to combine elements from different songs to create unique new compositions: Simply grab a beat from a Funkadelic track, a bassline from a Tito Puente piece, and fitting horns from a Fela Kuti song, and seamlessly integrate them into your DAW in record time. Using Polymath's search capability to discover related tracks, it is a breeze to create a polished, hour-long mash-up DJ set. For ML developers, Polymath simplifies the process of creating a large music dataset, for training generative models, etc.

## How does it work?
- Music Source Separation is performed with the [Demucs](https://github.com/facebookresearch/demucs) neural network
- Music Structure Segmentation/Labeling is performed with the [sf_segmenter](https://github.com/wayne391/sf_segmenter) neural network
- Music Pitch Tracking and Key Detection are performed with [Crepe](https://github.com/marl/crepe) neural network
- Music to MIDI transcription is performed with [Basic Pitch](https://github.com/spotify/basic-pitch) neural network
- Music Quantization and Alignment are performed with [pyrubberband](https://github.com/bmcfee/pyrubberband)
- Music Info retrieval and processing is performed with [librosa](https://github.com/librosa/librosa)

## Community

Join the Polymath Community on [Discord](https://discord.gg/gaZMZKzScj)

## Requirements

You need to have the following software installed on your system:

- ``ffmpeg``

## Installation

You need python version `>=3.7` and `<=3.10`. From your terminal run:
```bash
git clone https://github.com/samim23/polymath
cd polymath
pip install -r requirements.txt
```

## Docker setup

If you have [Docker](https://www.docker.com/) installed on your system, you can use the provided `Dockerfile` to quickly build a polymath docker image (if your user is not part of the `docker` group, remember to prepend `sudo` to the following command):

```bash
docker build -t polymath ./
```

In order to exchange input and output files between your hosts system and the polymath docker container, you need to create the following four directories:

- `./input`
- `./library`
- `./processed`
- `./separated`

Now put any files you want to process with polymath into the `input` folder.
Then you can run polymath through docker by using the `docker run` command and pass any arguments that you would originally pass to the python command, e.g. if you are in a linux OS call:

```bash
docker run \
    -v "$(pwd)"/processed:/polymath/processed \
    -v "$(pwd)"/separated:/polymath/separated \
    -v "$(pwd)"/library:/polymath/library \
    -v "$(pwd)"/input:/polymath/input \
    polymath python /polymath/polymath.py -a ./input/song1.wav
```

## Run Polymath

### 1. Add songs to the Polymath Library

##### Add YouTube video to library (auto-download)
```bash
python polymath.py -a n6DAqMFe97E
```
##### Add audio file (wav or mp3)
```bash
python polymath.py -a /path/to/audiolib/song.wav
```
##### Add multiple files at once
```bash
python polymath.py -a n6DAqMFe97E,eaPzCHEQExs,RijB8wnJCN0
python polymath.py -a /path/to/audiolib/song1.wav,/path/to/audiolib/song2.wav
python polymath.py -a /path/to/audiolib/
```
Songs are automatically analyzed once which takes some time. Once in the database, they can be access rapidly. The database is stored in the folder "/library/database.p". To reset everything, simply delete it.

### 2. Quantize songs in the Polymath Library
##### Quantize a specific songs in the library to tempo 120 BPM (-q = database audio file ID, -t = tempo in BPM)
```bash
python polymath.py -q n6DAqMFe97E -t 120
```
##### Quantize all songs in the library to tempo 120 BPM
```bash
python polymath.py -q all -t 120
```
##### Quantize a specific songs in the library to the tempo of the song (-k)
```bash
python polymath.py -q n6DAqMFe97E -k
```
Songs are automatically quantized to the same tempo and beat-grid and saved to the folder “/processed”.

### 3. Search for similar songs in the Polymath Library
##### Search for 10 similar songs based on a specific songs in the library (-s = database audio file ID, -sa = results amount)
```bash
python polymath.py -s n6DAqMFe97E -sa 10
```
##### Search for similar songs based on a specific songs in the library and quantize all of them to tempo 120 BPM
```bash
python polymath.py -s n6DAqMFe97E -sa 10 -q all -t 120
```
##### Include BPM as search criteria  (-st)
```bash
python polymath.py -s n6DAqMFe97E -sa 10 -q all -t 120 -st -k
```
Similar songs are automatically found and optionally quantized and saved to the folder "/processed". This makes it easy to create for example an hour long mix of songs that perfectly match one after the other. 

### 4. Convert Audio to MIDI
##### Convert all processed audio files and stems to MIDI (-m)
```bash
python polymath.py -a n6DAqMFe97E -q all -t 120 -m
```
Generated Midi Files are currently always 120BPM and need to be time adjusted in your DAW. This will be resolved [soon](https://github.com/spotify/basic-pitch/issues/40). The current Audio2Midi model gives mixed results with drums/percussion. This will be resolved with additional audio2midi model options in the future.


## Audio Features

### Extracted Stems
The Demucs Neural Net has settings that can be adjusted in the python file
```bash
- bass
- drum
- guitare
- other
- piano
- vocals
```
### Extracted Features
The audio feature extractors have settings that can be adjusted in the python file
```bash
- tempo
- duration
- timbre
- timbre_frames
- pitch
- pitch_frames
- intensity
- intensity_frames
- volume
- avg_volume
- loudness
- beats
- segments_boundaries
- segments_labels
- frequency_frames
- frequency
- key
```

## License
Polymath is released under the MIT license as found in the [LICENSE](https://github.com/samim23/polymath/blob/main/LICENSE) file.
