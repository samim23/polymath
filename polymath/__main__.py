#!/usr/bin/env python

##########################################
################ POLYMATH ################
############## by samim.io ###############
##########################################

import os
import pickle
import argparse

from polymath.extract import get_audio_features
from polymath.ingest import video_process, audio_directory_process, audio_process
from polymath.library import write_library, read_library
from polymath.nearest import get_nearest
from polymath.quantize import quantizeAudio


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
    parser.add_argument('-st', '--searchbpm', help='include BPM of audio files as similiarty search criteria"', required=False, action="store_true", default=False)
    parser.add_argument('-m', '--midi', help='extract midi from audio files"', required=False, action="store_true", default=False)

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

    # MIDI
    extractmidi = bool(args.midi)
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
            audio_features = get_audio_features(file=file,file_id=vid.id, extractMidi=extractmidi)

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
                    quantizeAudio(videos[idx], bpm=tempo, keepOriginalBpm = keepOriginalBpm, pitchShiftFirst = pitchShiftFirst, extractMidi = extractmidi)
                    break
                if vidarg == 'all' and len(newvids) == 0:
                    quantizeAudio(videos[idx], bpm=tempo, keepOriginalBpm = keepOriginalBpm, pitchShiftFirst = pitchShiftFirst, extractMidi = extractmidi)

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
                    quantizeAudio(query, bpm=tempo, keepOriginalBpm = keepOriginalBpm, pitchShiftFirst = pitchShiftFirst, extractMidi = extractmidi)
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
                        quantizeAudio(query, bpm=tempo, keepOriginalBpm = keepOriginalBpm, pitchShiftFirst = pitchShiftFirst, extractMidi = extractmidi)
                    i += 1
                break

if __name__ == "__main__":
    main()
