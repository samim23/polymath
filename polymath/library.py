import pickle

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


class Video:
    def __init__(self,name,video,audio):
        self.id = ""
        self.url = ""
        self.name = name
        self.video = video
        self.audio = audio
        self.video_features = []
        self.audio_features = []
