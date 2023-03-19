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
