import os

import librosa
import pyrubberband as pyrb
import soundfile as sf

from polymath.midi import extractMIDI


def quantizeAudio(vid, bpm=120, keepOriginalBpm = False, pitchShiftFirst = False, extractMidi = False):
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

    audiofilepaths = []
    # save audio to disk
    path = os.path.join(os.getcwd(), 'processed', path_prefix + " - " + path_suffix +'.wav')
    sf.write(path, strechedaudio, sr)
    audiofilepaths.append(path)

    # process stems
    stems = ['bass', 'drums', 'guitar', 'other', 'piano', 'vocals']
    for stem in stems:
        path = os.path.join(os.getcwd(), 'separated', 'htdemucs_6s', vid.id, stem +'.wav')
        print(f"- Quantize Audio: {stem}")
        y, sr = librosa.load(path, sr=None)
        strechedaudio = pyrb.timemap_stretch(y, sr, time_map)
        # save stems to disk
        path = os.path.join(os.getcwd(), 'processed', path_prefix + " - Stem " + stem + " - " + path_suffix +'.wav')
        sf.write(path, strechedaudio, sr)
        audiofilepaths.append(path)

    # metronome click (optinal)
    click = False
    if click:
        clicks_audio = librosa.clicks(times=fixed_beat_times, sr=sr)
        print(len(clicks_audio), len(strechedaudio))
        clicks_audio = clicks_audio[:len(strechedaudio)]
        path = os.path.join(os.getcwd(), 'processed', vid.id + '- click.wav')
        sf.write(path, clicks_audio, sr)

    if extractMidi:
        output_dir = os.path.join(os.getcwd(), 'processed')
        extractMIDI(audiofilepaths, output_dir)
