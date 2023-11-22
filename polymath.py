#!/usr/bin/env python
# ruff: noqa: T201
"""Polymath.py - Playing with your music library.

Polymath uses machine learning to convert any music library
(e.g from Hard-Drive or YouTube) into a music production sample-library.
"""

import argparse
import os
import random
import string
import tempfile

import librosa
from nendo import Nendo, NendoConfig, NendoTrack
from yt_dlp import YoutubeDL


def import_youtube(nendo, yt_id):
    """Import the audio from the given youtube ID into the library.

    Args:
        nendo (Nendo): The nendo instance to use.
        yt_id (str): ID of the youtube video.

    Returns:
        NendoTrack: The imported track.
    """
    # check if id already in db
    db_tracks = nendo.library.find_tracks(value=yt_id)
    if len(db_tracks) > 0:
        print(f"Track with youtube id {yt_id} already exists in library. Skipping.")
        return None

    # analyse videos and save to disk
    url = f"https://www.youtube.com/watch?v={yt_id}"
    with tempfile.TemporaryDirectory() as temp_dir:
        ydl_opts = {
            "quiet": True,
            "outtmpl": temp_dir + "/%(id)s.%(ext)s",
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "vorbis",
                    "preferredquality": "192",
                },
            ],
        }
        with YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(url, download=True)
        video = result["entries"][0] if "entries" in result else result
        return nendo.library.add_track(
            file_path=f"{temp_dir}/{video['id']}.ogg",
            meta={
                "original_info": video["id"],
            },
        )

def input_tracks(nendo, input_string):
    """Import a list of tracks from youtube and local FS.

    Args:
        nendo (Nendo): The Nendo instance to use.
        input_string (str): Comma-separated list of items to import into the
            polymath library.
    """
    input_items = input_string.split(",")
    for item in input_items:
        if os.path.isdir(item):
            nendo.add_tracks(path=item)
        elif os.path.isfile(item):
            nendo.add_track(file_path=item)
        else:
            import_youtube(nendo, item)
        print(f"Added {item}")

def process_tracks(
    nendo,
    tracks,
    analyze,
    stemify,
    quantize,
    quantize_to_bpm,
    loopify,
    n_loops,
    beats_per_loop,
):
    """Process the given list of NendoTracks using Nendo plugins.

    Args:
        nendo (Nendo): The Nendo instance to use.
        tracks (List[NendoTrack]): List of tracks to process.
        analyze (bool): Flag determining whether to analyze as part of processing.
        stemify (bool): Flag determining whether to stemify as part of processing.
        quantize (bool): Flag determining whether to quantize as part of processing.
        quantize_to_bpm (int): Target bpm for quantization.
        loopify (bool): Flag determining whether to loopify as part of processing.
        n_loops (int): Number of loops to extract.
        beats_per_loop (int): Beats per loop to extract.
    """
    n = 0
    for track in tracks:
        original_title = track.meta["title"]
        print(f"Processing track {1}/{len(tracks)}: {original_title}")
        duration = round(librosa.get_duration(y=track.signal, sr=track.sr), 3)
        if (analyze is True and (
            len(
                track.get_plugin_data(
                    plugin_name="nendo_plugin_classify_core",
                ),
            ) == 0  or nendo.config.replace_plugin_data is True)
        ):
            print("Analyzing...")
            track.process("nendo_plugin_classify_core")
            # analysis_data = track.get_plugin_data(
            #     plugin_name="nendo_plugin_classify_core",
            # )
        stems = track
        if (stemify is True and
            track.track_type != "stem" and
            "has_stems" not in track.resource.meta):
            print("Stemifying...")
            stems = track.process("nendo_plugin_stemify_demucs")
            track.set_meta({"has_stems": True })
            for stem in stems:
                stem_type = stem.get_meta("stem_type")
                stem.meta = dict(track.meta)
                stem.set_meta(
                    {
                        "title": f"{original_title} - {stem_type} stem",
                        "stem_type": stem_type,
                        "duration": duration,
                    },
                )
        quantized = stems
        if quantize is True:
            print("Quantizing...")
            quantized = stems.process(
                "nendo_plugin_quantize_core",
                bpm=quantize_to_bpm,
            )
            if type(quantized) == NendoTrack: # is a single track
                if not quantized.has_related_track(track_id=track.id, direction="from"):
                    quantized.relate_to_track(
                        track_id=track.id,
                        relationship_type="quantized",
                    )
                quantized.meta = dict(track.meta)
                duration = round(librosa.get_duration(y=quantized.signal, sr=quantized.sr), 3)
                quantized.set_meta(
                    {
                        "title": f"{original_title} - ({quantize_to_bpm} bpm)",
                        "duration": duration,
                    },
                )
            else:  # is a collection
                for j, qt in enumerate(quantized):
                    if not qt.has_related_track(track_id=track.id, direction="from"):
                        qt.relate_to_track(
                            track_id=track.id,
                            relationship_type="quantized",
                        )
                    qt.meta = dict(track.meta)
                    duration = round(librosa.get_duration(y=qt.signal, sr=qt.sr), 3)
                    if stems[j].track_type == "stem":
                        qt.set_meta(
                            {
                                "title": (
                                    f"{original_title} - "
                                    f"{stems[j].meta['stem_type']} "
                                    f"({quantize_to_bpm} bpm)"
                                ),
                                "stem_type": stems[j].meta["stem_type"],
                                "duration": duration,
                            },
                        )
                    else:
                        qt.set_meta(
                            {
                                "title": f"{original_title} ({quantize_to_bpm} bpm)",
                                "duration": duration,
                            },
                        )
        loopified = quantized
        if loopify is True:
            print("Loopifying...")
            loopified = []
            if type(quantized) == NendoTrack:
                quantized = [quantized]
            for qt in quantized:
                qt_loops = qt.process(
                    "nendo_plugin_loopify",
                    n_loops=n_loops,
                    beats_per_loop=beats_per_loop,
                )
                loopified += qt_loops
                num_loop = 1
                for lp in qt_loops:
                    if not lp.has_related_track(track_id=track.id, direction="from"):
                        lp.relate_to_track(
                            track_id=track.id,
                            relationship_type="loop",
                        )
                    stem_type = qt.meta["stem_type"] if qt.has_meta("stem_type") else ""
                    qt_info = (
                        f" ({quantize_to_bpm} bpm)"
                        if qt.track_type == "quantized"
                        else ""
                    )
                    lp.meta = dict(track.meta)
                    duration = round(librosa.get_duration(y=lp.signal, sr=lp.sr), 3)
                    lp.set_meta(
                        {
                            "title": f"{original_title} - {stem_type} loop {num_loop} {qt_info}",
                            "duration": duration,
                        },
                    )
                    num_loop += 1
        n = n+1
        print(f"Track {n}/{len(tracks)} Done.\n")
    print("Processing completed. "
          f"The library now contains {len(nendo.library)} tracks.")

def export_tracks(nendo, tracks, output_folder, export_format):
    """Export the given tracks to the given output folder in the given format.

    Args:
        nendo (Nendo): The Nendo instance to use.
        tracks (List[NendoTrack]): List of track to export.
        output_folder (str): Output path.
        export_format (str): Output format.
    """
    if os.path.exists(output_folder) is False:
        os.mkdir(output_folder)

    print(f"Exporting {len(tracks)} tracks")
    for found_track in tracks:
        bpm = ""
        bpm_pd = found_track.get_plugin_data(
            key="tempo",
        )
        if not isinstance(bpm_pd, list) and len(bpm_pd) != 0:
            bpm = f"_{int(float(bpm_pd))}bpm"
        stem = (
            f"_{found_track.get_meta('stem_type')}" if
            found_track.has_meta("stem_type") else
            ""
        )
        track_type = (
            f"_{found_track.track_type}" if
            found_track.track_type != "track" else
            ""
        )
        alphabet = string.ascii_lowercase + string.digits
        rnd = "".join(random.choices(alphabet, k=6))  # noqa: S311
        file_path = (
            f"{output_folder}/{found_track.meta['title']}"
            f"{stem}{track_type}{bpm}"
            f"_{rnd}.{export_format}"
        )
        exported_path = nendo.library.export_track(
            track_id=found_track.id,
            file_path=file_path,
        )
        print(f"Exported track {exported_path}")

def parse_args() -> argparse.Namespace:  # noqa: D103
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        required=False,
        help=("Comma-separated list of tracks to add to the polymath library."
              "Tracks can be either youtube IDs, file paths or directories."
        ),
    )
    parser.add_argument(
        "-p",
        "--process",
        required=False,
        action="store_true",
        help=(
            "Flag that enables all processing steps "
            "(use -q aswell to specify target bpm)."
        ),
    )
    parser.add_argument(
        "-a",
        "--analyze",
        required=False,
        action="store_true",
        help="Flag to enable running the analysis plugin.",
    )
    parser.add_argument(
        "-s",
        "--stemify",
        required=False,
        action="store_true",
        help="Flag to enable running the stemify plugin.",
    )
    parser.add_argument(
        "-q",
        "--quantize",
        required=False,
        type=int,
        help="Quantize tracks to given bpm (default is 120).",
    )
    parser.add_argument(
        "-l",
        "--loopify",
        required=False,
        action="store_true",
        help="Flag to enable running the loopify plugin.",
    )
    parser.add_argument(
        "-ln",
        "--loop_num",
        type=int,
        default=1,
        help="Number of loops to extract (requires -l, default is 1).",
    )
    parser.add_argument(
        "-lb",
        "--loop_beats",
        type=int,
        default=8,
        help="Number of beats per loop (requires -l, default is 8).",
    )
    parser.add_argument(
        "-f",
        "--find",
        required=False,
        type=str,
        help=(
            "Find specific tracks to apply polymath. "
            "Omit to work with all tracks."
        ),
    )
    parser.add_argument(
        "-bmin",
        "--bpm_min",
        required=False,
        type=int,
        help="Find tracks with a minimum bpm provided by this paramter.",
    )
    parser.add_argument(
        "-bmax",
        "--bpm_max",
        required=False,
        type=int,
        help="Find tracks with a maximum bpm provided by this paramter.",
    )
    parser.add_argument(
        "-fs",
        "--find_stems",
        required=False,
        action="store_true",
        help="Flag to enable finding stems.",
    )
    parser.add_argument(
        "-st",
        "--stem_type",
        choices=["any", "vocals", "drums", "bass", "other"],
        default="any",
        help="Flag to enable searching for stems.",
    )
    parser.add_argument(
        "-fl",
        "--find_loops",
        required=False,
        action="store_true",
        help="Flag to enable finding loops.",
    )
    parser.add_argument(
        "-e",
        "--export",
        required=False,
        action="store_true",
        help="Flag to enable exporting of tracks.",
    )
    parser.add_argument(
        "-o",
        "--output_path",
        type=str,
        default="polymath_output",
        help="Output path for file export.",
    )
    parser.add_argument(
        "-of",
        "--output_format",
        choices=["wav", "mp3", "ogg"],
        default="wav",
        help="Output path for file export.",
    )
    parser.add_argument(
        "-lp",
        "--library_path",
        default="polymath_library",
        type=str,
        help="Path to the polymath library directory.",
    )
    return parser.parse_args()


def main():  # noqa: D103
    args = parse_args()

    nendo = Nendo(
        config=NendoConfig(
            log_level="error",
            library_path=args.library_path,
            skip_duplicate=True,
            plugins=[
                "nendo_plugin_classify_core",
                "nendo_plugin_quantize_core",
                "nendo_plugin_stemify_demucs",
                "nendo_plugin_loopify",
            ],
        ),
    )

    if args.input:
        input_tracks(nendo, args.input)

    if (
        args.process or
        args.analyze or
        args.stemify or
        (args.quantize is not None) or
        args.loopify
    ):
        # apply search
        tracks = []
        if args.find is None:
            tracks = nendo.filter_tracks(track_type="track")
        else:
            for search_value in args.find.split(","):
                tracks = tracks + nendo.filter_tracks(
                    search_meta={"": search_value},
                    track_type="track",
            )

        if args.process:
            process_tracks(
                nendo = nendo,
                tracks = tracks,
                analyze = True,
                stemify = True,
                quantize = True,
                quantize_to_bpm = args.quantize or 120,
                loopify = True,
                n_loops = args.loop_num,
                beats_per_loop = args.loop_beats,
            )
        else:
            process_tracks(
                nendo = nendo,
                tracks = tracks,
                analyze = args.analyze,
                stemify = args.stemify,
                quantize = args.quantize is not None,
                quantize_to_bpm = args.quantize if args.quantize is not None else 120,
                loopify = args.loopify,
                n_loops = args.loop_num,
                beats_per_loop = args.loop_beats,
            )

    if args.export and args.output_path is not None:
        if args.find is not None:
            search_values = args.find.split(",")
            search_meta = { f"arg{i}": search_values[i] for i in range(len(search_values)) }
        track_type = ["track"]
        if args.find_stems is True:
            track_type.append("stem")
        if args.find_loops is True:
            track_type.append("loop")
        if args.find is None:
            track_type.append("quantized")
        filters = {}
        if args.bpm_min is not None or args.bpm_max is not None:
            track_type.append("quantized")
            bpm_min = args.bpm_min or 0
            bpm_max = args.bpm_max or 999
            filters.update({"tempo": (float(bpm_min), float(bpm_max))})

        found_tracks = nendo.filter_tracks(
            filters=filters if len(filters) > 0 else None,
            track_type=track_type,
            search_meta=search_meta if args.find is not None else None,
        )
        found_tracks = [
            ft for ft in found_tracks if (
                 not ft.has_meta("stem_type") or
                 (args.find_stems is True and
                  (args.stem_type == "any" or
                   ft.get_meta("stem_type") == args.stem_type)))
        ]
        export_tracks(
            nendo=nendo,
            tracks=found_tracks,
            output_folder=args.output_path,
            export_format=args.output_format,
        )


if __name__ == "__main__":
    main()
