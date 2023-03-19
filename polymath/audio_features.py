import sys
from math import pow, log2

import crepe
import librosa
import numpy as np
from sf_segmenter import Segmenter

neg80point8db = 0.00009120108393559096
bit_depth = 16
default_silence_threshold = (neg80point8db * (2 ** (bit_depth - 1))) * 4


def root_mean_square(data):
    return float(np.sqrt(np.mean(np.square(data))))


def loudness_of(data):
    return root_mean_square(data)


def normalized(list):
    """Given an audio buffer, return it with the loudest value scaled to 1.0"""
    return list.astype(np.float32) / float(np.amax(np.abs(list)))


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
    S = librosa.feature.melspectrogram(y, sr=sr, n_mels=128)
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


