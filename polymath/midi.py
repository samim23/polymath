from basic_pitch.inference import predict_and_save


def extractMIDI(audio_paths, output_dir):
    print('- Extract Midi')
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
