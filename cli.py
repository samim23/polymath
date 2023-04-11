from internals.media import Media
from internals.processors import AudioProcessor,VideoProcessor
from internals import utils
from internals.db import TinyDBWrapper
import fire


utils.PathConfig.initFolders()
utils.createDBFile(utils.PathConfig.dbDir, utils.PathConfig.dbFile)
utils.printPolymath()

db = TinyDBWrapper(utils.PathConfig.dbFile)

def splitStems(cleanedFile:str, stemsOutputDir:str = str(utils.PathConfig.stemsDir)) -> None:
    # check if audio is clean
    print("splitting stems")
    AudioProcessor.split_stems(cleanedFile, stemsOutputDir)

def addSong(songPath: str, ss: bool = False) -> None:
    """
    Overview
    --------
    Process a single song from local hard drive,\nthen add it to the database


    Parameters
    ----------
    songPath : str
        Path to song to be added

    Returns
    -------
    None

    """

    # check if song exists and is a valid file
    songPath = utils.strictFile(
        songPath,
        lambda: print(
            f"The path you specified is not a valid file path:\n\t{songPath}"
        ),
    ).allowedExtensions([".mp3", ".wav"])

    # generate song ID
    # The id will look like this: "song_name_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z"
    songID = Media.generateID(songPath.path.replace(" ", "_"))
    print(f"Song ID: {songID}")

    
    def upsert() -> str:
        cleanedFile, features, frequencyFrames = db.upsertSong(
                        songPath.path, 
                        songID, 
                        str(utils.PathConfig.processed),
                        str(utils.PathConfig.frequencyFramesOutDir),
                        )
        return cleanedFile

        
    # add song to db if not already there
    if not db.idExists(songID):
        cleanedFile = upsert()
        if ss:
            splitStems(cleanedFile, utils.PathConfig().stemsDir)

    # if song is already in db, ask if user wants to overwrite
    else:
        ii = input(
            f"""
                   {songPath.pathObj.stem} is already in the database with the following ID: {songID}
                   Do you want to overwrite it? (y/n): """
        )

        # if user wants to overwrite, update the song
        if ii.lower() == "y":
            cleanedFile = upsert()
            if ss:
                splitStems(cleanedFile, str(utils.PathConfig.stemsDir))
        # if user doesn't want to overwrite, exit
        else:
            print("Goodbye")
            exit()

def addVideo(youtubeUrl: str, ss: bool = False) -> None:
    """
    Overview
    --------
    Extract the audio from a SINGLE youtube video and add it to the database\n
    Will not accept a playlist url, only a single video url

    Parameters
    ----------
    youtubeUrl : str
        The url of the youtube video to be added

    ss : bool, optional
        Whether or not to split the stems, by default False

    Returns
    -------
    None

    """
    if not VideoProcessor.is_youtube_url(youtubeUrl):
        print(f"The url you entered is not a youtube url: {youtubeUrl}")
        return

    if VideoProcessor.is_playlist(youtubeUrl):
        print(
            f"""The url you entered is a playlist url:\n\t{youtubeUrl} 
            \nPlease enter a video url instead
            \nUse the 'addPlaylist' command to add a playlist"""
        )
        return

    """
    Begin processing the video
    """
    info = VideoProcessor.get_video_info_filtered(youtubeUrl)

    # The id will look like this: "Ciara - Da Girls [Official Video]_M2z-RZR0P3Y"
    id = info["title"].replace(" ", "_") + "_" + info["id"]

    def upsert() -> str:
        mp3 = VideoProcessor.download_audio(
            youtubeUrl, str(utils.PathConfig.ytdl_content), format="mp3"
        )
        
        cleanedFile, features, frequencyFrames = db.upsertSong(
                        mp3, 
                        id, 
                        str(utils.PathConfig.processed),
                        str(utils.PathConfig.frequencyFramesOutDir),
                        )
        return cleanedFile

    
    if not db.idExists(id):
        # add song to db, split stems if specified and seperate frequency frames into their own text file
        cleanedFile = upsert()
        
        if ss:
            splitStems(cleanedFile, str(utils.PathConfig.stemsDir))
    else:
        # Let user know that the song is already in the database
        # Ask if they want to overwrite it
        ii = input(
            f"""
                   {info['title']} is already in the database with the following ID: {id}
                   Do you want to overwrite it? (y/n): """
        )

        # if user wants to overwrite, update the song
        if ii.lower() == "y":
            cleanedFile = upsert()
            
            if ss:
                splitStems(cleanedFile, str(utils.PathConfig.stemsDir))
        # if user doesn't want to overwrite, exit
        else:
            print("Goodbye")
            exit()

def allSongs() -> None:
    """ """
    return db.tdb.all()

# def rmSong(songID: str) -> None:
#     """ """
#     pass


# # def addPlaylist(): -> None:

# # def addSongs() -> None:
# #     '''
# #     process one or more songs
# #     '''
# #     pass


# # def addVideos() -> None:
# #     '''
# #     Process one or more videos
# #     '''
# #     pass

# # def audioToMidi(audioPath:str) -> None:
# #     '''

# #     '''
# #     pass

# # def search(query:str) -> None:
# #     '''

# #     '''
# #     pass

if __name__ == "__main__":
    fire.Fire(
        {
            "addSong": addSong,
            "addVideo": addVideo,
            "all": allSongs,
            "splitStems": splitStems,
            'mp32wav': AudioProcessor.mp3ToWav,
        }
    )
