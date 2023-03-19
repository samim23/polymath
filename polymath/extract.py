import os
import subprocess

import librosa
import numpy as np

from polymath.audio_features import get_segments, get_pitch_dnn, get_average_pitch, get_intensity, get_pitch, \
    get_timbre, get_volume
from polymath.midi import extractMIDI


def stemsplit(destination, demucsmodel):
    subprocess.run(["demucs", destination, "-n", demucsmodel]) #  '--mp3'


def get_audio_features(file,file_id,extractMidi = False):
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
    CQT_sync = get_intensity(y, sr, beats)
    C_sync = get_pitch(y_harmonic, sr, beats)
    M_sync = get_timbre(y, sr, beats)
    volume, avg_volume, loudness = get_volume(file)

    print('7/8 feature aggregation')
    intensity_frames = np.matrix(CQT_sync).getT()
    pitch_frames = np.matrix(C_sync).getT()
    timbre_frames = np.matrix(M_sync).getT()

    print('8/8 split stems')
    stemsplit(file, 'htdemucs_6s')

    if extractMidi:
        audiofilepaths = []
        stems = ['bass', 'drums', 'guitar', 'other', 'piano', 'vocals']
        for stem in stems:
            path = os.path.join(os.getcwd(), 'separated', 'htdemucs_6s', file_id, stem +'.wav')
            audiofilepaths.append(path)
        output_dir = os.path.join(os.getcwd(), 'separated', 'htdemucs_6s', file_id)
        extractMIDI(audiofilepaths, output_dir)

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
