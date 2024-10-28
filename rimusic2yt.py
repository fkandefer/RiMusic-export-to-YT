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
import os

import pandas as pd
import google.oauth2.credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from tqdm import tqdm

SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]


# authenticate function
def authenticate():
    """
    User authentication via OAuth2 for accessing the YouTube API.
    It checks for an existing token and refreshes it if needed.

    Returns:
        creds: The authenticated credentials file to be used with YouTube API.
    """
    creds = None
    if os.path.exists("token.json"):
        creds = google.oauth2.credentials.Credentials.from_authorized_user_file(
            "token.json", SCOPES
        )

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "client_secret.json", SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return creds


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
    >>> get_youtube_playlist_name('RMPlaylist_MyPlaylist_20221010.csv')
    '2022-10-10 MyPlaylist'

    >>> get_youtube_playlist_name('RMPlaylist_SummerHits_20230915.csv')
    '2023-09-15 SummerHits'

    Filename not matching the pattern:
    >>> get_youtube_playlist_name('InvalidFileName.csv')
    '... InvalidFileName.csv'
    """
    m = re.search(r"^RMPlaylist_(.*)_([^_]*)\.csv$", file)
    if m is None:
        return f"{datetime.datetime.now().isoformat()[:10]} {file}"
    name, time = m.groups()
    return f"{time[:4]}-{time[4:6]}-{time[6:8]} {name}"


def create_playlist(api, name):
    """
    Creates a new YouTube playlist using the provided name.

    Args:
        api: An authenticated YouTube API service object.
        name (str): The name of the playlist to create.

    Returns:
        The response containing the details of the created playlist.
    """
    request = api.playlists().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": name,
            },
            "status": {
                "privacyStatus": "public"  # you can change it to unlisted or private
            },
        },
    )
    response = request.execute()
    return response


def process_playlist(path: PathLike, playlist_name: str | None = None):
    """
    Processes a playlist file exported from RiMusic.

    This function reads the playlist file, extracts its name, and
    uploads it as a new playlist to YouTube. It adds each video (by
    its MediaId) from the playlist CSV to the created YouTube playlist.

    Args:
        path (Pathlike): The path to the playlist file.
        playlist_name (str, optional): The name of the playlist.
            If None, it will be extracted from the filename using
            `get_youtube_playlist_name`. Defaults to None.

    Raises:
        AssertionError: If the file does not exist or is not a CSV.
    """
    path = Path(path)
    assert path.exists(), f"File `{path}` does not exist."
    assert path.is_file(), f"Path `{path}` is not a file."
    assert path.suffix == ".csv", f"File `{path}` is not a CSV file."

    if playlist_name is None:
        playlist_name = get_youtube_playlist_name(path.name)

    print(f"Processing playlist: {playlist_name}")

    creds = authenticate()
    # read from csv file
    data = pd.read_csv(path)
    media_id = data["MediaId"]
    try:
        youtube = build("youtube", "v3", credentials=creds)

        playlist = create_playlist(youtube, playlist_name)

        print(f"Playlist created: {playlist_name}")

        # adding song to playlist
        for song in tqdm(media_id):
            request = youtube.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": playlist["id"],
                        "resourceId": {"kind": "youtube#video", "videoId": song},
                    }
                },
            )
            request.execute()
    except HttpError as e:
        print(f"An error occurred: {e}")


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

    parser.add_argument(
        "playlist_name",
        type=str,
        help="The name of the playlist to be created on YouTube.",
        nargs="?",
    )

    args = parser.parse_args()

    process_playlist(args.csv_playlist, args.playlist_name)


if __name__ == "__main__":
    main()
