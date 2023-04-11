from tinydb import TinyDB, Query
from pathlib import Path
from .processors import AudioProcessor
from .utils import writeFrequencyFramesToFile
from dataclasses import dataclass


@dataclass
class TinyDBWrapper:
    pathToDb: str

    def __post_init__(self):
        self.pathToDb = Path(self.pathToDb)
        if not self.pathToDb.exists():
            self.pathToDb.touch()
        self.tdb = TinyDB(self.pathToDb)

    def idExists(self, id: str) -> bool:
        """
        Overview
        ---------
        Check if a song ID exists in the database

        Parameters
        ----------
        id : str
            ID of song

        Returns
        -------
        bool
            True if song exists, False if not

        """
        return bool(self.tdb.search(Query().id == id))

    
    def upsertSong(
        self,
        songPath: str,
        songID: str,
        cleanedAudioOutputPath: str,
        frequencyFramesOutputDir: str,
        separateFrequencyFrames: bool = True,
        #update: bool = False,
    ) -> tuple[str, dict[str, str], list[list[float]]]:
        """
        Overview
        --------
        This function grabs the cleaned file, features, and frequency frames,\n
        then writes the frequency frames to a text file
        and inserts the song into the database
        
        If update is True, then the song will be updated if it already exists

        Parameters
        ----------
        songPath : str
            Path to the song to be added

        songID : str
            ID of the song to be added

        splitStems : bool, optional
            Whether to split the stems or not, by default False

        Returns
        -------
            cleanedFile: str
                Path to the cleaned file
            features: dict[str, str]
                Dictionary of features
            frequencyFrames: list[list[float]]
                List of frequency frames
        """
        cleanedFile, features, frequencyFrames = AudioProcessor.processSong(
            songPath, songID, cleanedAudioOutputPath, separateFrequencyFrames=True
        )

        data = {
            "id": songID,
            "songName": Path(songPath).stem,
            "pathToFile": cleanedFile,
            
            # Convert the features to strings 
            # then add the frequency frames path with the pipe operator
            "features": {k: str(v) for (k, v) in features.items()}
            | {
                "frequencyFramesPath": writeFrequencyFramesToFile(
                    songID, frequencyFrames, frequencyFramesOutputDir
                )
            }
            if separateFrequencyFrames
            else {"frequencyFrames": frequencyFrames},
        }
        
        
        self.tdb.upsert(data, Query().id == songID)
        print(f"Song in db: {songPath}")
        return cleanedFile, features, frequencyFrames

