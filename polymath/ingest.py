import fnmatch
import hashlib
import os
import shutil
import subprocess

import librosa
import numpy as np
import soundfile as sf

from yt_dlp import YoutubeDL

from polymath.library import write_library, Video


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
