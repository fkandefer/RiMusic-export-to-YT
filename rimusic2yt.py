#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RiMusic to YouTube Playlist Importer

Import playlists exported from RiMusic to YouTube.
"""

from os import PathLike
import argparse
from argparse import RawDescriptionHelpFormatter

def process_playlist(path: PathLike, playlist_name: str | None = None):
    # TODO: implement the function
    pass

def main():
    """
    Main function that creates the argument parser and processes the provided argument.
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=RawDescriptionHelpFormatter
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
