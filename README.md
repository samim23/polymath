
# Polymath

Polymath uses machine learning to convert any music library (e.g from hard-drive or YouTube) into a music production sample-library. All songs are automatically separated into stems *(beats, bass, etc.)*, quantized to the same tempo and beat-grid *(e.g. 120bpm)* and made sortable by musical structure *(e.g. verse, chorus, etc.)* and key (*e.g C4, E3, etc.*). Polymath is a game-changing workflow for music producers and DJs (and ML audio devs)

<p align="center"><img  width="95%"  src="https://samim.io/static/upload/Fl4g_z4XkAEfDS_.jpeg"  /></p>

**Use-case example:** With Polymath you can very easily grab a baseline from a Funkadelic tune, grab a beat from an Tito Puente tune, grab horns from a Fela Kuti tune and mash them together in your DAW.

## How does it work?
- Music Source Separation is performed with Facebook's [Demucs](https://github.com/facebookresearch/demucs) neural network
- Music Structure Segmentation/Labeling is performed with the [sf_segmenter](https://github.com/wayne391/sf_segmenter) neural network
- Music Pitch Tracking and Key Detection are performed with [Crepe](https://github.com/marl/crepe) neural network
- Music Quantization and Alignment are performed with [pyrubberband](https://github.com/bmcfee/pyrubberband)
- Music Info Retrieval is performed with [librosa](https://github.com/librosa/librosa)

## Installation

You will need at least Python 3.7. From your terminal run:
```bash
git clone git@github.com:samim23/polymath.git
cd polymath
pip install -r requirements.txt
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
##### Quantize a specific songs in the library to tempo 120 BPM
```bash
python polymath.py -q n6DAqMFe97E -t 120
```
##### Quantize all songs in the library
```bash
python polymath.py -q all -t 120
```
##### Quantize a specific songs in the library to the tempo of the song
```bash
python polymath.py -q n6DAqMFe97E -k
```
Songs are automatically quantized to the same tempo and beat-grid and saved to the folder “/processed”.

### 3. Search for similar songs in the Polymath Library
##### Search for similar songs based on a specific songs in the library (-s = query audio file ID, -sa = results amount)
```bash
python polymath.py -s n6DAqMFe97E -sa 10 -q all
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

## License
Polymath is released under the MIT license as found in the [LICENSE](https://github.com/samim23/polymath/blob/main/LICENSE) file.
