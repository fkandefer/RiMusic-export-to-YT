#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RiMusic to YouTube Playlist Importer

Import playlists exported from RiMusic to YouTube.
"""

from os import PathLike
import argparse
import re
import datetime
from pathlib import Path


def get_youtube_playlist_name(file: str) -> str:
    """
    Extracts and formats the playlist name and date from a filename.

    Args:
        file (str): The name of the file.

    Returns:
        str: A formatted string representing the playlist name and
        date, or a string with the current date if the pattern is
        not matched.

    Examples:
    >>> youtube_playlist_name('RMPlaylist_MyPlaylist_20221010.csv')
    '2022-10-10 MyPlaylist'

    >>> youtube_playlist_name('RMPlaylist_SummerHits_20230915.csv')
    '2023-09-15 SummerHits'

    Filename not matching the pattern:
    >>> youtube_playlist_name('InvalidFileName.csv')
    '... InvalidFileName.csv'
    """
    m = re.search(r"^RMPlaylist_(.*)_([^_]*)\.csv$", file)
    if m is None:
        return f"{datetime.datetime.now().isoformat()[:10]} {file}"
    name, time = m.groups()
    return f"{time[:4]}-{time[4:6]}-{time[6:8]} {name}"


def process_playlist(path: PathLike, playlist_name: str | None = None):
    """
    Processes a playlist file exported from RiMusic.

    Args:
        path (Pathlike): The path to the playlist file.
        playlist_name (str, optional): The name of the playlist.
        If None, it will be extracted from the filename using
        `get_youtube_playlist_name`. Defaults to None.

    Raises:
        AssertionError: If the path is not a CSV file.
    """
    path = Path(path)
    assert path.exists(), f"File `{path}` does not exist."
    assert path.is_file(), f"Path `{path}` is not a file."
    assert path.suffix == ".csv", f"File `{path}` is not a CSV file."

    if playlist_name is None:
        playlist_name = get_youtube_playlist_name(path.name)

    print(f"Processing playlist: {playlist_name}")

    # TODO: Implement the processing of the playlist file.
    # media = import_playlist(path)
    # export_playlist(media, playlist_name)


def main():
    """
    Main function that creates the argument parser and processes the provided argument.
    """
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "csv_playlist",
        type=str,
        help="The playlist exported from RiMusic to be processed by the script.",
    )

    # TODO: add an optional argument to specify the playlist name

    args = parser.parse_args()

    process_playlist(args.csv_playlist)


if __name__ == "__main__":
    main()
