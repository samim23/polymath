import os
import sys
import subprocess
import shutil
from math import log2, pow
import numpy as np
import librosa
import crepe
import soundfile as sf
import pyrubberband as pyrb
import re

# from yt_dlp import YoutubeDL
from sf_segmenter.segmenter import Segmenter

# import tensorflow as tf
# from basic_pitch import ICASSP_2022_MODEL_PATH

# from basic_pitch.inference import predict
from dataclasses import dataclass
from pathlib import Path

#  field
# from typing import Any, List
# from abc import ABCMeta, abstractmethod
from yt_dlp import YoutubeDL


@dataclass
class VideoProcessor:
    """
    Handles video processing
    """

    def audio_extract(vidobj, file):
        print("audio_extract", file)
        command = (
            "ffmpeg -hide_banner -loglevel panic -i "
            + file
            + " -ab 160k -ac 2 -ar 44100 -vn -y "
            + vidobj.audio
        )
        subprocess.call(command, shell=True)
        return vidobj.audio

    def is_youtube_url(url: str) -> bool:
        if "youtube.com/" in url:
            return True
        if "youtu.be/" in url:
            return True
        return False

    def get_url_type(url: str) -> str:
        return (
            1
            if "youtube.com/watch?v=" in url
            else 2
            if "youtu.be/" in url
            else 3
            if "youtube.com/playlist"
            else 0
        )

    def download_video(
        url: str,
        outdir: str,
        format: str = "mp4",
    ):
        if not Path(outdir).exists():
            raise Exception(
                f"The output directory you supplied does not exist \n \n outdir: {outdir} \n \n url: {url} \n \n"
            )

        if not Path(outdir).is_dir():
            raise Exception(
                f"The output directory you supplied is not a directory \n \n outdir: {outdir} \n \n url: {url} \n \n"
            )

        ydl_opts = {
            "outtmpl": outdir,
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best--merge-output-format mp4",
        }
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download(url)
        # return Path(outdir) /

    def download_audio(
        url: str,
        outdir: str,
        format: str = "mp3",
    ) -> str:
        '''
        Overview
        --------
        Download audio from a youtube url
        
        Parameters
        ----------
        url : str
        outdir : str
        format : str
        
        Returns
        -------
        finalPath : str
            Path to the downloaded audio file
        
        '''
        
        # In case the format specifier has too many dots in it like "..mp3"
        format = format.lower().replace(".", "")
        
        if not Path(outdir).is_dir():
            raise Exception(
                f"The output directory you supplied is not a directory \n \n outdir: {outdir} \n \n url: {url} \n \n"
            )

        if not isinstance(format, str):
            raise Exception(
                f"The format you supplied is not a string \n \n format: {format} \n \n url: {url} \n \n"
            )
        if format not in ["mp3", "wav"]:
            raise Exception(
                f"The format you supplied is not a valid format \n \n format: {format} \n \n url: {url} \n \n"
            )

        if not isinstance(outdir, str):
            raise Exception(
                f"The outdir you supplied is not a string \n \n outdir: {outdir} \n \n url: {url} \n \n"
            )

        title = VideoProcessor.get_video_info_filtered(url)["title"]
        
        finalPath = str(Path(outdir) / str(title + "." + format))

        ydl_opts = {
            "outtmpl": str(Path(outdir) / "%(title)s.%(ext)s"),
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": format,
                    "preferredquality": "192",
                }
            ],
        }
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download(url)
            


        return finalPath

    def get_video_info_full(url: str) -> dict:
        """
        returns the full dictionary of video info
        """
        if not VideoProcessor.is_youtube_url(url):
            raise Exception(
                f"The url you supplied is not a youtube url \n \n url: {url} \n \n"
            )

        return YoutubeDL().extract_info(url, download=False)

    def get_video_info_filtered(url: str) -> dict:
        """
        Overview
        --------
        Grabbing the full dictionary of video info is a bit too much,\nso this function filters out the info we want.
        
        
        Returns 
        --------
            dict:
                A filtered dictionary of video info\n
                wanted_keys = (
                    "title",
                    "id",
                    "url",
                    "thumbnail",
                    "duration",
                    "description",
                    "resolution",
                    "tags",
                    "fps",
                    "playlist_index",
                    "playlist",
                )
        
        """
        if not VideoProcessor.is_youtube_url(url):
            raise Exception(
                f"The url you supplied is not a youtube url \n \n url: {url} \n \n"
            )

        dictfilt = lambda x, y: dict([(i, x[i]) for i in x if i in set(y)])
        wanted_keys = (
            "title",
            "id",
            "url",
            "thumbnail",
            "duration",
            "description",
            "resolution",
            "tags",
            "fps",
            "playlist_index",
            "playlist",
        )
        return dictfilt(YoutubeDL().extract_info(url, download=False), wanted_keys)

    def get_audio_from_video(videoPath: str, audioOutPath: str) -> str:
        """
        Extracts audio from video file

        and returns the path to the audio file
        """
        command = (
            "ffmpeg -hide_banner -loglevel panic -i "
            + videoPath
            + " -ab 160k -ac 2 -ar 44100 -vn -y "
            + audioOutPath
        )
        subprocess.call(command, shell=True)
        return audioOutPath

    def extract_video_id(url:str):
        """
        Extracts the video id from a YouTube URL.
        """
        if VideoProcessor.get_url_type(url) == 1:
            regex = r"watch\?v=(\S+)"
            match = re.search(regex, url)
            if match:
                return match.group(1).split("&")[0]
            else:
                return None
        elif VideoProcessor.get_url_type(url) == 2:
            return url.split("be/")[1].split("?")[0]
        elif VideoProcessor.get_url_type(url) == 3:
            return None
        else:
            raise Exception(f"Unknown URL type \n \n url: {url} \n \n")

    def is_playlist(url:str) -> bool:
        return True if VideoProcessor.extract_playlist_id(url) != None else False

    def extract_playlist_id(url:str):
        """
        Extracts the playlist id from a YouTube URL.
        """

        if VideoProcessor.get_url_type(url) == 1:
            regex = r"list=(\S+)"
            match = re.search(regex, url)
            if match:
                return match.group(1).split("&")[0]
            else:
                return None
        elif VideoProcessor.get_url_type(url) == 2:
            try:
                return url.split("list=")[1]
            except:
                return None
        elif VideoProcessor.get_url_type(url) == 3:
            return url.split("playlist?list=")[1]
        else:
            raise Exception(f"Unknown URL type \n \n url: {url} \n \n")


@dataclass
class AudioProcessor:

    """
    Handles all audio processing
    """

    neg80point8db: float = 0.00009120108393559096
    bit_depth: int = 16
    default_silence_threshold: float = (neg80point8db * (2 ** (bit_depth - 1))) * 4

    def resampleAudio(audioArray, sampleRate, targetSampleRate=44100) -> np.ndarray:
        return librosa.resample(
            audioArray, orig_sr=sampleRate, target_sr=targetSampleRate
        )

    def getAudioData(songPath: str, sr=None, mono=False) -> tuple[np.ndarray, int]:
        """
        y:
            Is a numpy array that contains the audio signal.
            Each value in the array represents the amplitude of the audio signal at a specific point in time.

        sr:
            Is the sampling rate of the audio signal.
            Specifies the number of samples per second in the audio signal.
        """
        y, sr = librosa.load(path=songPath, sr=sr, mono=mono)
        return y, sr

    @staticmethod
    def mp3ToWav(songPath: str, outputDir: str, songID: str) -> str:
        import wave
        """
        Convert mp3 to wav and return the path to the wav file
        """

        # if this is not an mp3 file raise an exception
        if not songPath.endswith(".mp3"):
            raise Exception(f"File is not an mp3: {songPath}")

        # if outPath does not exist raise an exception
        if not Path(outputDir).exists():
            raise Exception(f"Outpath does not exist: {outputDir}")

        songName = Path(songPath).name

        print("Converting mp3 to wav: ", songName)

        songArray, sampleRate = AudioProcessor.getAudioData(songPath)

        # resample to 44100k if required
        if sampleRate != 44100:
            print("converting audio file to 44100:", songName)
            songArray = AudioProcessor.resampleAudio(songArray, sampleRate, 44100)

        # If the file is stereo, convert to mono by averaging the left and right channels
        if songArray.ndim > 1:
            songArray = np.mean(songArray, axis=0)
        """
        write the wav file to the library folder
        """
        
        finalPath = str(Path(outputDir) / str(songID + ".wav"))
        sf.write(finalPath, np.ravel(songArray), 44100)
        return finalPath


    def cleanAudio(songPath: str, songID: str, outputDir: str) -> str:
        """
        Overview
        ---------
        Create a useable WAV file to later process


        Parameter
        ---------
        songPath : str
            path to the song
        songID : str
            unique ID for the song
        outputDir : str
            path to the output directory

        Returns
        -------
        str
            path to the cleaned audio file


        """
        if not Path(outputDir).exists():
            raise Exception(f"Outpath does not exist: {outputDir}")

        songName = Path(songPath).name

        print("Cleaning Audio :", songName)

        if songName.endswith(".mp3"):
            cleanedFile = AudioProcessor.mp3ToWav(songPath, outputDir, songID)

        # check if is wav and copy it to local folder
        elif songName.endswith(".wav"):
            audioArray, sampleRate = AudioProcessor.getAudioData(songPath)

            finalPath = str(
                Path(songPath).stem + "_" + songID + ".wav"
            )  # str(Path(outputDir) / "test.wav") #

            if sampleRate != 44100:
                print("Sample rate is not 44100:", sampleRate)
                print("Converting wav file to 44100:", songName)
                data = AudioProcessor.resampleAudio(audioArray, sampleRate, 44100)
                sf.write(finalPath, data, 44100)
            else:
                shutil.copy2(songPath, finalPath)

            cleanedFile = finalPath

        return cleanedFile

    ################## AUDIO FEATURES ##################

    def root_mean_square(data):
        return float(np.sqrt(np.mean(np.square(data))))

    def loudness_of(data):
        return AudioProcessor.root_mean_square(data)

    def normalized(audioBuffer: list) -> list:
        """
        Given an audio buffer, return it with the loudest value scaled to 1.0

        """
        return audioBuffer.astype(np.float32) / float(np.amax(np.abs(audioBuffer)))

    def start_of(list, threshold=default_silence_threshold, samples_before=1):
        """
        takes three arguments:
            a list of audio samples,
            a threshold value for silence detection (defaulting to default_silence_threshold if not provided),
            and a number of samples to look back before the detected start of audio (defaulting to 1 if not provided).

        The function returns the index of the start of audio in the input list.
        """
        if int(threshold) != threshold:
            threshold = threshold * float(2 ** (AudioProcessor.bit_depth - 1))
        index = np.argmax(np.absolute(list) > threshold)
        if index > (samples_before - 1):
            return index - samples_before
        else:
            return 0

    def end_of(list, threshold=default_silence_threshold, samples_after=1):
        if int(threshold) != threshold:
            threshold = threshold * float(2 ** (AudioProcessor.bit_depth - 1))
        rev_index = np.argmax(np.flipud(np.absolute(list)) > threshold)
        if rev_index > (samples_after - 1):
            return len(list) - (rev_index - samples_after)
        else:
            return len(list)

    def trim_data(
        data,
        start_threshold=default_silence_threshold,
        end_threshold=default_silence_threshold,
    ):
        start = AudioProcessor.start_of(data, start_threshold)
        end = AudioProcessor.end_of(data, end_threshold)

        return data[start:end]

    def load_and_trim(file):
        y, rate = librosa.load(file, mono=True)
        y = AudioProcessor.normalized(y)
        trimmed = AudioProcessor.trim_data(y)
        return trimmed, rate

    def get_loudness(file):
        loudness = -1
        try:
            audio, rate = AudioProcessor.load_and_trim(file)
            loudness = AudioProcessor.loudness_of(audio)
        except Exception as e:
            sys.stderr.write(f"Failed to run on {file}: {e}\n")
        return loudness

    def get_volume(file):
        volume = -1
        avg_volume = -1
        try:
            audio, rate = AudioProcessor.load_and_trim(file)
            volume = librosa.feature.rms(y=audio)[0]
            avg_volume = np.mean(volume)
            loudness = AudioProcessor.loudness_of(audio)
        except Exception as e:
            sys.stderr.write(f"Failed to get Volume and Loudness on {file}: {e}\n")
        return volume, avg_volume, loudness

    def get_key(freq):
        A4 = 440
        C0 = A4 * pow(2, -4.75)
        name = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        h = round(12 * log2(freq / C0))
        octave = h // 12
        n = h % 12
        return name[n] + str(octave)

    def get_average_pitch(pitch):
        pitches = []
        confidences_thresh = 0.8
        i = 0
        while i < len(pitch):
            if pitch[i][2] > confidences_thresh:
                pitches.append(pitch[i][1])
            i += 1
        if len(pitches) > 0:
            average_frequency = np.array(pitches).mean()
            average_key = AudioProcessor.get_key(average_frequency)
        else:
            average_frequency = 0
            average_key = "A0"
        return average_frequency, average_key

    def get_intensity(y, sr, beats):
        # Beat-synchronous Loudness - Intensity
        CQT = librosa.cqt(y, sr=sr, fmin=librosa.note_to_hz("A1"))
        freqs = librosa.cqt_frequencies(CQT.shape[0], fmin=librosa.note_to_hz("A1"))
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
        S = librosa.feature.melspectrogram(y, sr=sr, n_mels=128)
        log_S = librosa.power_to_db(S, ref=np.max)
        # MFCC - Timbre
        mfcc = librosa.feature.mfcc(S=log_S, n_mfcc=13)
        delta_mfcc = librosa.feature.delta(mfcc)
        delta2_mfcc = librosa.feature.delta(mfcc, order=2)
        M = np.vstack([mfcc, delta_mfcc, delta2_mfcc])
        # Beat-synchronous MFCC - Timbre
        M_sync = librosa.util.sync(M, beats)
        return M_sync

    def get_segments(audio_file:str):
        segmenter = Segmenter()
        boundaries, labs = segmenter.proc_audio(audio_file)
        return boundaries, labs

    def get_pitch_dnn(audio_file:str):
        # DNN Pitch Detection
        pitch = []
        audio, sr = librosa.load(audio_file)
        time, frequency, confidence, activation = crepe.predict(
            audio,
            sr,
            model_capacity="tiny",
            viterbi=True,
            center=True,
            step_size=10,
            verbose=1,
        )  # tiny|small|medium|large|full
        i = 0
        while i < len(time):
            pitch.append([time[i], frequency[i], confidence[i]])
            i += 1
        return pitch

    def stemsplit(destination:str, demucsmodel:str):
        subprocess.run(["demucs", destination, "-n", demucsmodel])  #  '--mp3'

    def extractMIDI(audio_paths, output_dir:str):
        from basic_pitch.inference import predict_and_save

        print("- Extract Midi")
        save_midi = True
        sonify_midi = False
        save_model_outputs = False
        save_notes = False

        predict_and_save(
            audio_path_list=audio_paths,
            output_directory=output_dir,
            save_midi=save_midi,
            sonify_midi=sonify_midi,
            save_model_outputs=save_model_outputs,
            save_notes=save_notes,
        )

    def quantizeAudio(
        vid, bpm=120, keepOriginalBpm=False, pitchShiftFirst=False, extractMidi=False
    ):
        print(
            "Quantize Audio: Target BPM",
            bpm,
            "-- id:",
            vid.id,
            "bpm:",
            round(vid.audio_features["tempo"], 2),
            "frequency:",
            round(vid.audio_features["frequency"], 2),
            "key:",
            vid.audio_features["key"],
            "timbre:",
            round(vid.audio_features["timbre"], 2),
            "name:",
            vid.name,
            "keepOriginalBpm:",
            keepOriginalBpm,
        )

        # load audio file
        y, sr = librosa.load(vid.audio, sr=None)

        # Keep Original Song BPM
        if keepOriginalBpm:
            bpm = float(vid.audio_features["tempo"])
            print("Keep original audio file BPM:", vid.audio_features["tempo"])
        # Pitch Shift audio file to desired BPM first
        elif pitchShiftFirst:  # WORK IN PROGRESS
            print("Pitch Shifting audio to desired BPM", bpm)
            # Desired tempo in bpm
            original_tempo = vid.audio_features["tempo"]
            speed_factor = bpm / original_tempo
            # Resample the audio to adjust the sample rate accordingly
            sr_stretched = int(sr / speed_factor)
            y = librosa.resample(
                y=y, orig_sr=sr, target_sr=sr_stretched
            )  # ,  res_type='linear'
            y = librosa.resample(y, orig_sr=sr, target_sr=44100)

        # extract beat
        y_harmonic, y_percussive = librosa.effects.hpss(y)
        tempo, beats = librosa.beat.beat_track(
            sr=sr,
            onset_envelope=librosa.onset.onset_strength(y=y_percussive, sr=sr),
            trim=False,
        )
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
        original_length = len(y + 1)
        orig_end_diff = original_length - time_map[i][0]
        new_ending = int(round(time_map[i][1] + orig_end_diff * (tempo / bpm)))
        new_member = (original_length, new_ending)
        time_map.append(new_member)

        # time strech audio
        print("- Quantize Audio: source")
        strechedaudio = pyrb.timemap_stretch(y, sr, time_map)

        path_suffix = (
            f"Key {vid.audio_features['key']} - "
            f"Freq {round(vid.audio_features['frequency'], 2)} - "
            f"Timbre {round(vid.audio_features['timbre'], 2)} - "
            f"BPM Original {int(vid.audio_features['tempo'])} - "
            f"BPM {bpm}"
        )
        path_prefix = f"{vid.id} - {vid.name}"

        audiofilepaths = []
        # save audio to disk
        path = os.path.join(
            os.getcwd(), "processed", path_prefix + " - " + path_suffix + ".wav"
        )
        sf.write(path, strechedaudio, sr)
        audiofilepaths.append(path)

        # process stems
        stems = ["bass", "drums", "guitar", "other", "piano", "vocals"]
        for stem in stems:
            path = os.path.join(
                os.getcwd(), "separated", "htdemucs_6s", vid.id, stem + ".wav"
            )
            print(f"- Quantize Audio: {stem}")
            y, sr = librosa.load(path, sr=None)
            strechedaudio = pyrb.timemap_stretch(y, sr, time_map)
            # save stems to disk
            path = os.path.join(
                os.getcwd(),
                "processed",
                path_prefix + " - Stem " + stem + " - " + path_suffix + ".wav",
            )
            sf.write(path, strechedaudio, sr)
            audiofilepaths.append(path)

        # metronome click (optinal)
        click = False
        if click:
            clicks_audio = librosa.clicks(times=fixed_beat_times, sr=sr)
            print(len(clicks_audio), len(strechedaudio))
            clicks_audio = clicks_audio[: len(strechedaudio)]
            path = os.path.join(os.getcwd(), "processed", vid.id + "- click.wav")
            sf.write(path, clicks_audio, sr)

        if extractMidi:
            output_dir = os.path.join(os.getcwd(), "processed")
            AudioProcessor.extractMIDI(audiofilepaths, output_dir)

        def get_audio_features(
            songPath: str, songID: str, extractMidi: bool = False
        ) -> dict:
            print(
                "------------------------------ get_audio_features:",
                songID,
                "------------------------------",
            )
            print("1/8 segementation")
            segments_boundaries, segments_labels = AudioProcessor.get_segments(songPath)

            print("2/8 pitch tracking")
            frequency_frames = AudioProcessor.get_pitch_dnn(songPath)
            average_frequency, average_key = AudioProcessor.get_average_pitch(
                frequency_frames
            )

            print("3/8 load sample")
            y, sr = librosa.load(songPath, sr=None)
            song_duration = librosa.get_duration(y=y, sr=sr)

            print("4/8 sample separation")
            y_harmonic, y_percussive = librosa.effects.hpss(y)

            print("5/8 beat tracking")
            tempo, beats = librosa.beat.beat_track(
                sr=sr,
                onset_envelope=librosa.onset.onset_strength(y=y_percussive, sr=sr),
                trim=False,
            )

            print("6/8 feature extraction")
            CQT_sync = AudioProcessor.get_intensity(y, sr, beats)
            C_sync = AudioProcessor.get_pitch(y_harmonic, sr, beats)
            M_sync = AudioProcessor.get_timbre(y, sr, beats)
            volume, avg_volume, loudness = AudioProcessor.get_volume(songPath)

            print("7/8 feature aggregation")
            intensity_frames = np.matrix(CQT_sync).getT()
            pitch_frames = np.matrix(C_sync).getT()
            timbre_frames = np.matrix(M_sync).getT()

            # print('8/8 split stems')
            # stemsplit(songPath, 'htdemucs_6s')

            if extractMidi:
                audiofilepaths = []
                stems = ["bass", "drums", "guitar", "other", "piano", "vocals"]
                for stem in stems:
                    path = os.path.join(
                        os.getcwd(), "separated", "htdemucs_6s", songID, stem + ".wav"
                    )
                    audiofilepaths.append(path)
                output_dir = os.path.join(
                    os.getcwd(), "separated", "htdemucs_6s", songID
                )
                AudioProcessor.extractMIDI(audiofilepaths, output_dir)

            audio_features = {
                "id": songID,
                "tempo": tempo,
                "duration(sec)": song_duration,
                "duration(mins)": song_duration / 60,
                "timbre": np.mean(timbre_frames),
                "timbre_frames": timbre_frames,
                "pitch": np.mean(pitch_frames),
                "pitch_frames": pitch_frames,
                "intensity": np.mean(intensity_frames),
                "intensity_frames": intensity_frames,
                "volume": volume,
                "avg_volume": avg_volume,
                "loudness": loudness,
                "beats": librosa.frames_to_time(beats, sr=sr),
                "segments_boundaries": segments_boundaries,
                "segments_labels": segments_labels,
                "frequency_frames": frequency_frames,
                "frequency": average_frequency,
                "key": average_key,
            }
            return audio_features

    def get_audio_features(
        songPath: str,
        songID: str,
        extractMidi: bool = False,
        separateFrequencyFrames: bool = False,
    ) -> dict | tuple[dict, list]:
        """
        Extracts audio features from a song and returns them as a dictionary.

        If separateFrequencyFrames is set to True, the function will return a tuple
        containing the audio features dictionary and a list of frequency frames.
        """
        print(
            "------------------------------ get_audio_features:",
            songID,
            "------------------------------",
        )

        print("1/8 segementation")
        segments_boundaries, segments_labels = AudioProcessor.get_segments(songPath)

        print("2/8 pitch tracking")
        frequency_frames = AudioProcessor.get_pitch_dnn(songPath)
        average_frequency, average_key = AudioProcessor.get_average_pitch(
            frequency_frames
        )

        print("3/8 load sample")
        y, sr = librosa.load(songPath, sr=None)
        song_duration = librosa.get_duration(y=y, sr=sr)

        print("4/8 sample separation")
        y_harmonic, y_percussive = librosa.effects.hpss(y)

        print("5/8 beat tracking")
        tempo, beats = librosa.beat.beat_track(
            sr=sr,
            onset_envelope=librosa.onset.onset_strength(y=y_percussive, sr=sr),
            trim=False,
        )

        print("6/8 feature extraction")
        CQT_sync = AudioProcessor.get_intensity(y, sr, beats)
        C_sync = AudioProcessor.get_pitch(y_harmonic, sr, beats)
        M_sync = AudioProcessor.get_timbre(y, sr, beats)
        volume, avg_volume, loudness = AudioProcessor.get_volume(songPath)

        print("7/8 feature aggregation")
        intensity_frames = np.matrix(CQT_sync).getT()
        pitch_frames = np.matrix(C_sync).getT()
        timbre_frames = np.matrix(M_sync).getT()

        if extractMidi:
            audiofilepaths = []
            stems = ["bass", "drums", "guitar", "other", "piano", "vocals"]
            for stem in stems:
                path = os.path.join(
                    os.getcwd(), "separated", "htdemucs_6s", songID, stem + ".wav"
                )
                audiofilepaths.append(path)
            output_dir = os.path.join(os.getcwd(), "separated", "htdemucs_6s", songID)
            AudioProcessor.extractMIDI(audiofilepaths, output_dir)

        audio_features = {
            "id": songID,
            "tempo": tempo,
            "duration": song_duration,
            "timbre": np.mean(timbre_frames),
            "timbre_frames": timbre_frames,
            "pitch": np.mean(pitch_frames),
            "pitch_frames": pitch_frames,
            "intensity": np.mean(intensity_frames),
            "intensity_frames": intensity_frames,
            "volume": volume,
            "avg_volume": avg_volume,
            "loudness": loudness,
            "beats": librosa.frames_to_time(beats, sr=sr),
            "segments_boundaries": segments_boundaries,
            "segments_labels": segments_labels,
            # "frequency_frames":frequency_frames,
            "frequency": average_frequency,
            "key": average_key,
        }
        return (
            audio_features,
            frequency_frames
            if separateFrequencyFrames
            else audio_features["frequency_frames"].append(frequency_frames),
        )

    @staticmethod
    def split_stems(audioFilePath:str, destination:str, demucsmodel:str = "htdemucs_6s"):
        '''
        Calls the demucs library to split the stems of a song
        '''
        
        #destination = str(destination)
        
        subprocess.run(["demucs", str(audioFilePath), "-o", str(destination), "-n", demucsmodel])  #  '--mp3'

    @staticmethod
    def processSong(
        songPath: str, 
        songID: str, 
        cleanedAudioOutputPath: str,
        separateFrequencyFrames: bool = False
    ) -> tuple[str, dict] | tuple[str, dict, list]:
        """
        
        Overview:
        --------
        This is the main entry point to process a song. 
        
        This function cleans the audio file, converts it to WAV 
        and places the WAV file in the processed folder

        Then it grabs the audio features and returns them
        
        Parameters:
        ---------
            songPath: str
                Path to the song
            songID: str
                ID of the song
            separateFrequencyFrames: bool
                If set to True, the function will return a tuple containing the audio features
                dictionary and a list of frequency frames.
            
        
        Returns:
        --------
        tuple[str, dict] | tuple[str, dict, list]:
            If separateFrequencyFrames is set to True, the function will return a tuple


        """
        # Path to the cleaned file
        cleanedFile = AudioProcessor.cleanAudio(songPath, songID, cleanedAudioOutputPath) # PathConfig.processed

        if separateFrequencyFrames:
            features, frequencyFrames = AudioProcessor.get_audio_features(
                cleanedFile, songID, separateFrequencyFrames=True
            )
            return cleanedFile, features, frequencyFrames

        # get features as a dict
        features = AudioProcessor.get_audio_features(cleanedFile, songID)
        return cleanedFile, features
