from pathlib import Path
from dataclasses import dataclass



@dataclass
class strictFile:
    path: str
    ifErr: callable = None

    def __post_init__(self):
        if not Path(self.path).is_file():
            if self.ifErr:
                self.ifErr()
            else:
                raise Exception(f"File not found: {self.path}")
        self.pathObj = Path(self.path)

    def allowedExtensions(self, allowedExtensionsList: list) -> object:
        '''
        If the file extension is not in the list of allowed extensions\n
        An exception will be raised
        '''
        if not allowedExtensionsList:
            return self
        
        allowedExtensionsList = [item.lower() for item in allowedExtensionsList]
        
        if self.pathObj.suffix.lower() not in allowedExtensionsList:
            raise Exception(f"File extension not allowed: {self.pathObj.suffix.lower()}")
        return self
	

 
@dataclass
class PathConfig:
    '''
    PathConfig is a dataclass that contains all the paths used in the project\n
    All paths are relative to the root of the project\n
    And are stored as Path objects
    
    Accessing the paths like this will return a Path object:
        PathConfig.dbFile
    
    Accessing the paths like this will return a string:
        PathConfig().dbFile
    
    '''
    
    thisFile: Path = Path(__file__)

    
    # Directories
    internalsDir: Path = thisFile.parent
    contentDir: Path = internalsDir.parent / "content"

    '''
    /content
        /ytdl_content
        /processed
        /stems
            /htdemucs_6s
        /db
            /frequencyFrames
    '''
    ytdl_content: Path = contentDir / "ytdl_content"
    processed: Path = contentDir / "processed"
    stemsDir: Path = contentDir / "stems"
    #demucs: Path = separated / "htdemucs_6s"
    dbDir: Path = contentDir / "db"
    frequencyFramesOutDir: Path = dbDir / "frequencyFrames"
    
    # Files
    dbFile: Path = dbDir / "db.json"



    def __getattribute__(self,item):
        """
        PathConfig().attrib will return a str rather than a Path Object
        PathConfig.attrib will return a path Object
        """
        return eval(f"str(PathConfig.{item})")

    def checkAllPathsExist():
        """
        If any of the paths in PathConfig are bad
        an exception will be raised
        """
        for k, v in PathConfig.__annotations__.items():
            if not eval(f"PathConfig.{k}.exists()"):
                raise Exception(f'Path at "{k}" DOES NOT EXIST')

    def initFolder(folder: Path):
        if not folder.exists():
            try:
                folder.mkdir()
                print(f"Created folder at:\n\t{folder}")
            except Exception as e:
                print(e, f"Failed to create {folder} folder \n Exiting...")
                exit(1)

    def initFolders():
        '''
        Overview
        --------
        
        Create the following directories if they don't already exist:
            - ytdl_videos
            - db
                - frequencyFramesOutDir
            - processed
            - separated
            - demucs
            
        '''
        list(
            map(
                PathConfig.initFolder,
                [
                    PathConfig.contentDir,
                    PathConfig.processed, 
                    PathConfig.stemsDir, 
                    PathConfig.dbDir,
                    PathConfig.frequencyFramesOutDir,
                    PathConfig.ytdl_content,
                ]
            )
        )

def printPolymath():
    print(
        "---------------------------------------------------------------------------- "
    )
    print(
        "--------------------------------- POLYMATH --------------------------------- "
    )
    print(
        "---------------------------------------------------------------------------- "
    )


def createDBFile(dbDir:Path, dbFile:Path) -> None:
    """
    Create db.json file if it doesn't already exist
    
    Parameters
    ----------
    dbDir : Path
        Path to the db directory
    dbFile : Path
        Path to the db.json file
    """
    Path.mkdir(dbDir, exist_ok=True)
    Path(dbFile).touch(exist_ok=True)


def writeFrequencyFramesToFile( 
                                    songID: str, 
                                    frequencyFrames: list, 
                                    frequencyFramesOutputDir:str
                                ) -> str:
    """
    Overview
    --------
    Write the frequency frames to a text file
    
    Parameters
    ----------
    songID : str
        Song ID
    frequencyFrames : list
        List of frequency frames
    frequencyFramesOuputDir : str
        Path to the frequency frames text file

    Returns
    -------
    frequencyFramesPath : str
        Path to the frequency frames text file
    """
    # Path to the frequency frames file
    frequencyFramesPath = Path(frequencyFramesOutputDir) / f"{songID}_FrequencyFrames.txt"

    # Write the frequency frames to a file
    with open(frequencyFramesPath, "w") as f:
        f.write(str(frequencyFrames))

    return str(frequencyFramesPath)


