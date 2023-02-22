#!/usr/bin/env python


import os
import sys
import pickle
import argparse
import subprocess
import fnmatch
import hashlib
import shutil
from math import log2, pow

import numpy as np 
#import librosa
import crepe
#import soundfile as sf
#import pyrubberband as pyrb
from yt_dlp import YoutubeDL
#from sf_segmenter.segmenter import Segmenter

##########################################
################ POLYMATH ################
############## by samim.io ###############
##########################################

class Video:
    def __init__(self,name,video,audio):
        self.id = ""
        self.url = ""
        self.name = name
        self.video = video
        self.audio = audio
        self.video_features = []
        self.audio_features = []

### Library

LIBRARY_FILENAME = "library/database.p"

def write_library(videos):
    with open(LIBRARY_FILENAME, "wb") as lib:
        pickle.dump(videos, lib)


def read_library():
    try:
        with open(LIBRARY_FILENAME, "rb") as lib:
            return pickle.load(lib)
    except:
        print("No Database file found:", LIBRARY_FILENAME)
    return []


################## VIDEO PROCESSING ##################

def audio_extract(vidobj,file):
    print("audio_extract",file)
    command = "ffmpeg -hide_banner -loglevel panic -i "+file+" -ab 160k -ac 2 -ar 44100 -vn -y " + vidobj.audio
    subprocess.call(command,shell=True)
    return vidobj.audio

def video_download(vidobj,url):
    print("video_download",url)
    ydl_opts = {
    'outtmpl': 'library/%(id)s',
    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best--merge-output-format mp4',
    } 
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download(url)

    with ydl: result = ydl.extract_info(url, download=True)

    if 'entries' in result: video = result['entries'][0] # Can be a playlist or a list of videos
    else: video = result  # Just a video

    filename = f"library/{video['id']}.{video['ext']}"
    print("video_download: filename",filename,"extension",video['ext'])
    vidobj.id = video['id']
    vidobj.name = video['title']
    vidobj.video = filename
    vidobj.url = url
    return vidobj

def video_process(vids,videos):
    for vid in vids:
        print('------ process video',vid)
        # check if id already in db
        download_vid = True
        for video in videos:
            if video.id == vid:
                print("already in db",vid)
                download_vid = False
                break

        # analyse videos and save to disk
        if download_vid:
            video = Video(vid,vid,f"library/{vid}.wav")
            video = video_download(video,f"https://www.youtube.com/watch?v={vid}")
            audio_extract(video,video.video)
            videos.append(video)
            print("NAME",video.name,"VIDEO",video.video,"AUDIO",video.audio)
            write_library(videos)
            print("video_process DONE",len(videos))
    return videos

################## AUDIO PROCESSING ##################

def audio_directory_process(vids, videos):
    filesToProcess = []
    for vid in vids:
        path = vid
        pattern = "*.mp3"
        for filename in fnmatch.filter(os.listdir(path), pattern):
            filepath = os.path.join(path, filename)
            print(filepath)
            if os.path.isfile(filepath):
                filesToProcess.append(filepath)

    print('Found', len(filesToProcess), 'wav or mp3 files')
    if len(filesToProcess) > 0:
        videos = audio_process(filesToProcess, videos)
    return videos

def audio_process(vids, videos):
    for vid in vids:
        print('------ process audio',vid)
        # extract file name
        audioname = vid.split("/")[-1]
        audioname, _ = audioname.split(".")

        # generate a unique ID based on file path and name
        hash_object = hashlib.sha256(vid.encode())
        audioid = hash_object.hexdigest()
        audioid = f"{audioname}_{audioid}"

        # check if id already in db
        process_audio = True
        for video in videos:
            if video.id == audioid:
                print("already in db",vid)
                process_audio = False
                break

        # check if is mp3 and convert it to wav
        if vid.endswith(".mp3"):
            # convert mp3 to wav and save it
            print('converting mp3 to wav:', vid)
            y, sr = librosa.load(path=vid, sr=None, mono=False)
            path = os.path.join(os.getcwd(), 'library', audioid+'.wav')
            # resample to 44100k if required
            if sr != 44100:
                print('converting audio file to 44100:', vid)
                y = librosa.resample(y, orig_sr=sr, target_sr=44100)
            sf.write(path, np.ravel(y), 44100)
            vid = path

        # check if is wav and copy it to local folder
        elif vid.endswith(".wav"):
            path1 = vid
            path2 = os.path.join(os.getcwd(), 'library', audioid+'.wav')
            y, sr = librosa.load(path=vid, sr=None, mono=False)
            if sr != 44100:
                print('converting audio file to 44100:', vid)
                y = librosa.resample(y, orig_sr=sr, target_sr=44100)
                sf.write(path2, y, 44100)
            else:
                shutil.copy2(path1, path2)
            vid = path2

        # analyse videos and save to disk
        if process_audio:
            video = Video(audioname,'',vid)
            video.id = audioid
            video.url = vid
            videos.append(video)
            write_library(videos)
            print("Finished procesing files:",len(videos))
            
    return videos

################## AUDIO FEATURES ##################

def root_mean_square(data):
    return float(np.sqrt(np.mean(np.square(data))))

def loudness_of(data):
    return root_mean_square(data)

def normalized(list):
    """Given an audio buffer, return it with the loudest value scaled to 1.0"""
    return list.astype(np.float32) / float(np.amax(np.abs(list)))

neg80point8db = 0.00009120108393559096
bit_depth = 16
default_silence_threshold = (neg80point8db * (2 ** (bit_depth - 1))) * 4

def start_of(list, threshold=default_silence_threshold, samples_before=1):
    if int(threshold) != threshold:
        threshold = threshold * float(2 ** (bit_depth - 1))
    index = np.argmax(np.absolute(list) > threshold)
    if index > (samples_before - 1):
        return index - samples_before
    else:
        return 0

def end_of(list, threshold=default_silence_threshold, samples_after=1):
    if int(threshold) != threshold:
        threshold = threshold * float(2 ** (bit_depth - 1))
    rev_index = np.argmax(
        np.flipud(np.absolute(list)) > threshold
    )
    if rev_index > (samples_after - 1):
        return len(list) - (rev_index - samples_after)
    else:
        return len(list)

def trim_data(
    data,
    start_threshold=default_silence_threshold,
    end_threshold=default_silence_threshold
):
    start = start_of(data, start_threshold)
    end = end_of(data, end_threshold)

    return data[start:end]

def load_and_trim(file):
    y, rate = librosa.load(file, mono=True)
    y = normalized(y)
    trimmed = trim_data(y)
    return trimmed, rate

def get_loudness(file):
    loudness = -1
    try:
        audio, rate = load_and_trim(file)
        loudness = loudness_of(audio)
    except Exception as e:
        sys.stderr.write(f"Failed to run on {file}: {e}\n")
    return loudness

def get_volume(file):
    volume = -1
    avg_volume = -1
    try:
        audio, rate = load_and_trim(file)
        volume = librosa.feature.rms(y=audio)[0]
        avg_volume = np.mean(volume)
        loudness = loudness_of(audio)
    except Exception as e:
        sys.stderr.write(f"Failed to get Volume and Loudness on {file}: {e}\n")
    return volume, avg_volume, loudness

def get_key(freq):
    A4 = 440
    C0 = A4*pow(2, -4.75)
    name = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    h = round(12*log2(freq/C0))
    octave = h // 12
    n = h % 12
    return name[n] + str(octave)

def get_average_pitch(pitch):
    pitches = []
    confidences_thresh = 0.8
    i = 0
    while i < len(pitch):
        if(pitch[i][2] > confidences_thresh):
            pitches.append(pitch[i][1])
        i += 1
    if len(pitches) > 0:
        average_frequency = np.array(pitches).mean()
        average_key = get_key(average_frequency)
    else:
        average_frequency = 0
        average_key = "A0"
    return average_frequency,average_key

def get_intensity(y, sr, beats):
    # Beat-synchronous Loudness - Intensity
    CQT = librosa.cqt(y, sr=sr, fmin=librosa.note_to_hz('A1'))
    freqs = librosa.cqt_frequencies(CQT.shape[0], fmin=librosa.note_to_hz('A1'))
    perceptual_CQT = librosa.perceptual_weighting(CQT**2, freqs, ref=np.max)
    CQT_sync = librosa.util.sync(perceptual_CQT, beats, aggregate=np.median)
    return CQT_sync

def get_pitch(y_harmonic, sr, beats):
    # Chromagram
    C = librosa.feature.chroma_cqt(y=y_harmonic, sr=sr)
    # Beat-synchronous Chroma - Pitch
    C_sync = librosa.util.sync(C, beats, aggregate=np.median)
    return C_sync

def get_timbre(y, sr, beats):
    # Mel spectogram
    #S = librosa.feature.melspectrogram(y, sr=sr, n_mels=128)
    log_S = librosa.power_to_db(S, ref=np.max)
    # MFCC - Timbre
    mfcc = librosa.feature.mfcc(S=log_S, n_mfcc=13)
    delta_mfcc  = librosa.feature.delta(mfcc)
    delta2_mfcc = librosa.feature.delta(mfcc, order=2)
    M = np.vstack([mfcc, delta_mfcc, delta2_mfcc])
    # Beat-synchronous MFCC - Timbre
    M_sync = librosa.util.sync(M, beats)
    return M_sync

def get_segments(audio_file):
    segmenter = Segmenter()
    boundaries, labs = segmenter.proc_audio(audio_file)
    return boundaries,labs 

def get_pitch_dnn(audio_file):
    # DNN Pitch Detection
    pitch = []
    audio, sr = librosa.load(audio_file)
    time, frequency, confidence, activation = crepe.predict(audio, sr, model_capacity="tiny", viterbi=True, center=True, step_size=10, verbose=1) # tiny|small|medium|large|full
    i = 0
    while i < len(time):
        pitch.append([time[i],frequency[i],confidence[i]])
        i += 1
    return pitch

def stemsplit(destination, demucsmodel):
    subprocess.run(["demucs", destination, "-n", demucsmodel]) #  '--mp3'

def quantizeAudio(vid, bpm=120, keepOriginalBpm = False, pitchShiftFirst = False):
    print("Quantize Audio: Target BPM", bpm, 
        "-- id:",vid.id,
        "bpm:",round(vid.audio_features["tempo"],2),
        "frequency:",round(vid.audio_features['frequency'],2),
        "key:",vid.audio_features['key'],
        "timbre:",round(vid.audio_features['timbre'],2),
        "name:",vid.name,
        'keepOriginalBpm:', keepOriginalBpm
        )

    # load audio file
    y, sr = librosa.load(vid.audio, sr=None)

    # Keep Original Song BPM
    if keepOriginalBpm:
        bpm = float(vid.audio_features['tempo'])
        print('Keep original audio file BPM:', vid.audio_features['tempo'])
    # Pitch Shift audio file to desired BPM first
    elif pitchShiftFirst: # WORK IN PROGRESS
        print('Pitch Shifting audio to desired BPM', bpm)
        # Desired tempo in bpm
        original_tempo = vid.audio_features['tempo']
        speed_factor = bpm / original_tempo
        # Resample the audio to adjust the sample rate accordingly
        sr_stretched = int(sr / speed_factor)
        y = librosa.resample(y=y, orig_sr=sr, target_sr=sr_stretched) #,  res_type='linear'
        y = librosa.resample(y, orig_sr=sr, target_sr=44100)

    # extract beat
    y_harmonic, y_percussive = librosa.effects.hpss(y)
    tempo, beats = librosa.beat.beat_track(sr=sr, onset_envelope=librosa.onset.onset_strength(y=y_percussive, sr=sr), trim=False)
    beat_frames = librosa.frames_to_samples(beats)

    # generate metronome
    fixed_beat_times = []
    for i in range(len(beat_frames)):
        fixed_beat_times.append(i * 120 / bpm)
    fixed_beat_frames = librosa.time_to_samples(fixed_beat_times)

    # construct time map
    time_map = []
    for i in range(len(beat_frames)):
        new_member = (beat_frames[i], fixed_beat_frames[i])
        time_map.append(new_member)

    # add ending to time map
    original_length = len(y+1)
    orig_end_diff = original_length - time_map[i][0]
    new_ending = int(round(time_map[i][1] + orig_end_diff * (tempo / bpm)))
    new_member = (original_length, new_ending)
    time_map.append(new_member)

    # time strech audio
    print('- Quantize Audio: source')
    strechedaudio = pyrb.timemap_stretch(y, sr, time_map)

    path_suffix = (
        f"Key {vid.audio_features['key']} - "
        f"Freq {round(vid.audio_features['frequency'], 2)} - "
        f"Timbre {round(vid.audio_features['timbre'], 2)} - "
        f"BPM Original {int(vid.audio_features['tempo'])} - "
        f"BPM {bpm}"
    )
    path_prefix = (
        f"{vid.id} - {vid.name}"
    )

    # save audio to disk
    path = os.path.join(os.getcwd(), 'processed', path_prefix + " - " + path_suffix +'.wav')
    sf.write(path, strechedaudio, sr)

    # process stems
    stems = ['bass', 'drums', 'guitar', 'other', 'piano', 'vocals']
    for stem in stems:
        path = os.path.join(os.getcwd(), 'separated', 'htdemucs_6s', vid.id, stem +'.wav')
        print(f"- Quantize Audio: {stem}")
        y, sr = librosa.load(path, sr=None)
        strechedaudio = pyrb.timemap_stretch(y, sr, time_map)
        # save stems to disk
        path = os.path.join(os.getcwd(), 'processed', path_prefix + " Stem" + stem + " - " + path_suffix +'.wav')
        sf.write(path, strechedaudio, sr)

    # metronome click (optinal)
    click = False
    if click:
        clicks_audio = librosa.clicks(times=fixed_beat_times, sr=sr)
        print(len(clicks_audio), len(strechedaudio))
        clicks_audio = clicks_audio[:len(strechedaudio)] 
        path = os.path.join(os.getcwd(), 'processed', vid.id + '- click.wav')
        sf.write(path, clicks_audio, sr)


def get_audio_features(file,file_id):
    print("------------------------------ get_audio_features:",file_id,"------------------------------")
    print('1/8 segementation')
    segments_boundaries,segments_labels = get_segments(file)
   
    print('2/8 pitch tracking')
    frequency_frames = get_pitch_dnn(file)
    average_frequency,average_key = get_average_pitch(frequency_frames)
    
    print('3/8 load sample')
    y, sr = librosa.load(file, sr=None)
    song_duration = librosa.get_duration(y=y, sr=sr)
    
    print('4/8 sample separation')
    y_harmonic, y_percussive = librosa.effects.hpss(y)
    
    print('5/8 beat tracking')
    tempo, beats = librosa.beat.beat_track(sr=sr, onset_envelope=librosa.onset.onset_strength(y=y_percussive, sr=sr), trim=False)

    print('6/8 feature extraction')
    #CQT_sync = get_intensity(y, sr, beats)
    #C_sync = get_pitch(y_harmonic, sr, beats)
    #M_sync = get_timbre(y, sr, beats)
    volume, avg_volume, loudness = get_volume(file)
   
    print('7/8 feature aggregation')
    #intensity_frames = np.matrix(CQT_sync).getT()
    #pitch_frames = np.matrix(C_sync).getT()
    #timbre_frames = np.matrix(M_sync).getT()

    print('8/8 split stems')
    stemsplit(file, 'htdemucs_6s')

    audio_features = {
        "id":file_id,
        "tempo":tempo,
        "duration":song_duration,
        "timbre":np.mean(timbre_frames),
        "timbre_frames":timbre_frames,
        "pitch":np.mean(pitch_frames),
        "pitch_frames":pitch_frames,
        "intensity":np.mean(intensity_frames),
        "intensity_frames":intensity_frames,
        "volume": volume,
        "avg_volume": avg_volume,
        "loudness": loudness,
        "beats":librosa.frames_to_time(beats, sr=sr),
        "segments_boundaries":segments_boundaries,
        "segments_labels":segments_labels,
        "frequency_frames":frequency_frames,
        "frequency":average_frequency,
        "key":average_key
    }
    return audio_features

################## SEARCH NEAREST AUDIO ##################

previous_list = []

def get_nearest(query,videos,querybpm, searchforbpm):
    global previous_list
    # print("Search: query:", query.name, '- Incl. BPM in search:', searchforbpm)
    nearest = {}
    smallest = 1000000000
    smallestBPM = 1000000000
    smallestTimbre = 1000000000
    smallestIntensity = 1000000000
    for vid in videos:
        if vid.id != query.id:
            comp_bpm = abs(querybpm - vid.audio_features['tempo'])
            comp_timbre = abs(query.audio_features["timbre"] - vid.audio_features['timbre'])
            comp_intensity = abs(query.audio_features["intensity"] - vid.audio_features['intensity'])
            #comp = abs(query.audio_features["pitch"] - vid.audio_features['pitch'])
            comp = abs(query.audio_features["frequency"] - vid.audio_features['frequency'])

            if searchforbpm:
                if vid.id not in previous_list and comp < smallest and comp_bpm < smallestBPM:# and comp_timbre < smallestTimbre:
                    smallest = comp
                    smallestBPM = comp_bpm
                    smallestTimbre = comp_timbre
                    nearest = vid
            else:
                if vid.id not in previous_list and comp < smallest:
                    smallest = comp
                    smallestBPM = comp_bpm
                    smallestTimbre = comp_timbre
                    nearest = vid
            #print("--- result",i['file'],i['average_frequency'],i['average_key'],"diff",comp)
    # print(nearest)
    previous_list.append(nearest.id)
   
    if len(previous_list) >= len(videos)-1:
        previous_list.pop(0)
        # print("getNearestPitch: previous_list, pop first")
    # print("get_nearest",nearest.id)
    return nearest

def getNearest(k, array):
    k = k / 10 # HACK
    return min(enumerate(array), key=lambda x: abs(x[1]-k))


################## MAIN ##################

def main():
    print("---------------------------------------------------------------------------- ")
    print("--------------------------------- POLYMATH --------------------------------- ")
    print("---------------------------------------------------------------------------- ")
    # Load DB
    videos = read_library()

    for directory in ("processed", "library", "separated", "separated/htdemucs_6s"):
        os.makedirs(directory, exist_ok=True)
    
    # Parse command line input
    parser = argparse.ArgumentParser(description='polymath')
    parser.add_argument('-a', '--add', help='youtube id', required=False)
    parser.add_argument('-r', '--remove', help='youtube id', required=False)
    parser.add_argument('-v', '--videos', help='video db length', required=False)
    parser.add_argument('-t', '--tempo', help='quantize audio tempo in BPM', required=False, type=float)
    parser.add_argument('-q', '--quantize', help='quantize: id or "all"', required=False)
    parser.add_argument('-k', '--quantizekeepbpm', help='quantize to the BPM of the original audio file"', required=False, action="store_true", default=False)
    parser.add_argument('-s', '--search', help='search for musically similar audio files, given a database id"', required=False)
    parser.add_argument('-sa', '--searchamount', help='amount of results the search returns"', required=False, type=int)
    parser.add_argument('-st', '--searchbpm', help='Include BPM of audio files as similiarty search criteria"', required=False, action="store_true", default=False)
    args = parser.parse_args()

    # List of videos to use
    if args.videos is not None:
        finalvids = []
        vids = args.videos.split(",")
        print("process selected videos only:",vids)
        for vid in vids:
            v = [x for x in videos if x.id == vid][0]
            finalvids.append(v)
        videos = finalvids

    # List of videos to delete
    if args.remove is not None:
        print("remove video:",args.remove)
        for vid in videos:
            if vid.id == args.remove:
                videos.remove(vid)
                break
        write_library(videos)

    # List of videos to download
    newvids = []
    if args.add is not None:
        print("add video:",args.add,"to videos:",len(videos))
        vids = args.add.split(",")
        if "/" in args.add and not (args.add.endswith(".wav") or args.add.endswith(".mp3")):
            print('add directory with wav or mp3 files')
            videos = audio_directory_process(vids,videos)
        elif ".wav" in args.add or ".mp3" in args.add:
            print('add wav or mp3 file')
            videos = audio_process(vids,videos)
        else:
            videos = video_process(vids,videos)
        newvids = vids
    
    # List of audio to quantize
    vidargs = []
    if args.quantize is not None:
        vidargs = args.quantize.split(",")
        # print("Quantize:", vidargs)
        if vidargs[0] == 'all' and len(newvids) != 0:
            vidargs = newvids

    # Tempo
    tempo = int(args.tempo or 120)

    # Quanize: Keep bpm of original audio file
    keepOriginalBpm = bool(args.quantizekeepbpm)

    # WIP: Quanize: Pitch shift before quanize
    pitchShiftFirst = False
    # if args.quantizepitchshift:
    #     pitchShiftFirst = True

    # Analyse to DB
    print(f"------------------------------ Files in DB: {len(videos)} ------------------------------")
    dump_db = False
    # get/detect audio metadata
    for vid in videos:
        feature_file = f"library/{vid.id}.a"
        # load features from disk
        if os.path.isfile(feature_file):
            with open(feature_file, "rb") as f:
                audio_features = pickle.load(f)
        # extract features
        else:
            # Is audio file from disk
            if len(vid.id) > 12: 
                print('is audio', vid.id, vid.name, vid.url)
                file = vid.url
                # if is mp3 file
                if vid.url[-3:] == "mp3":
                    file = os.path.join(os.getcwd(), 'library', vid.id + '.wav')
            # Is audio file extracted from downloaded video
            else:
                file = os.path.join(os.getcwd(), 'library', vid.id + '.wav')

            # Audio feature extraction
            audio_features = get_audio_features(file=file,file_id=vid.id)

            # Save to disk
            with open(feature_file, "wb") as f:
                pickle.dump(audio_features, f)
        
        # assign features to video
        vid.audio_features = audio_features
        print(
            vid.id,
            "tempo", round(audio_features["tempo"], 2),
            "duration", round(audio_features["duration"], 2),
            "timbre", round(audio_features["timbre"], 2),
            "pitch", round(audio_features["pitch"], 2),
            "intensity", round(audio_features["intensity"], 2),
            "segments", len(audio_features["segments_boundaries"]),
            "frequency", round(audio_features["frequency"], 2),
            "key", audio_features["key"],
            "name", vid.name,
        )
        #dump_db = True
    if dump_db:
        write_library(videos)

    print("--------------------------------------------------------------------------")

    # Quantize audio
    if args.search is None:
        for vidarg in vidargs:
            for idx, vid in enumerate(videos):
                if vid.id == vidarg:
                    quantizeAudio(videos[idx], bpm=tempo, keepOriginalBpm = keepOriginalBpm, pitchShiftFirst = pitchShiftFirst)
                    break
                if vidarg == 'all' and len(newvids) == 0:
                    quantizeAudio(videos[idx], bpm=tempo, keepOriginalBpm = keepOriginalBpm, pitchShiftFirst = pitchShiftFirst)

    # Search
    searchamount = int(args.searchamount or 20)
    searchforbpm = bool(args.searchbpm)

    if args.search is not None:
        for vid in videos:
            if vid.id == args.search:
                query = vid
                print(
                    'Audio files related to:', query.id,
                    "- Key:", query.audio_features['key'],
                    "- Tempo:", int(query.audio_features['tempo']),
                    ' - ', query.name,
                )
                if args.quantize is not None:
                    quantizeAudio(query, bpm=tempo, keepOriginalBpm = keepOriginalBpm, pitchShiftFirst = pitchShiftFirst)
                i = 0
                while i < searchamount:
                    nearest = get_nearest(query, videos, tempo, searchforbpm)
                    query = nearest
                    print(
                        "- Relate:", query.id,
                        "- Key:", query.audio_features['key'],
                        "- Tempo:", int(query.audio_features['tempo']),
                        ' - ', query.name,
                    )
                    if args.quantize is not None:
                        quantizeAudio(query, bpm=tempo, keepOriginalBpm = keepOriginalBpm, pitchShiftFirst = pitchShiftFirst)
                    i += 1
                break

if __name__ == "__main__":
    main()
