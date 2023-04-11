from dataclasses import dataclass
import hashlib
from pathlib import Path

@dataclass
class Media:
    id: str
    name: str

    def generateID(mediaPath: str) -> str:
        '''
        Overview
        ---------
        
        Creates a unique ID for a media file By hashing the file stem  
        String should look like: "songName_1234567890abcdef1234567890abcdef"

        Parameter
        ---------
        mediaPath : str
            Path to media file

        Returns
        -------
        str:
            return f"{name}_{hashStr}"
            should look like: "songName_1234567890abcdef1234567890abcdef"
        

        '''
        name = Path(mediaPath).stem
        hashStr = hashlib.sha256(mediaPath.encode()).hexdigest()
        return f"{name}_{hashStr}"

# @dataclass
# class Video(Media):
#     url: str  
#     video_features: List = field(default_factory=lambda: [])
#     audio_features: List = field(default_factory=lambda: [])

# @dataclass
# class Audio(Media):
#     path: str  