#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RiMusic to YouTube Playlist Importer

Import playlists exported from RiMusic to YouTube.
"""

import argparse
import datetime
import os
import re
from pathlib import Path

import google.oauth2.credentials
import pandas as pd
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


def process_playlist(data: pd.DataFrame, playlist_name: str):
    """
    Processes a playlist file exported from RiMusic.

    This function reads the playlist data, extracts its name, and
    uploads it as a new playlist to YouTube. It adds each video (by
    its MediaId) from the playlist DataFrame to the created YouTube playlist.

    Args:
        data (pd.DataFrame): The playlist data.
        playlist_name (str): The name of the playlist to be created on YouTube.

    Raises:
        AssertionError: If the file does not exist or is not a CSV.
    """

    print(f"Processing playlist: {playlist_name}")

    creds = authenticate()
    media_id = data["MediaId"]
    try:
        youtube = build("youtube", "v3", credentials=creds)

        playlist = create_playlist(youtube, playlist_name)

        url = f"https://www.youtube.com/playlist?list={playlist['id']}"
        print(f"New playlist created: {url}")

        # adding song to playlist
        for song in tqdm(media_id):

            request = youtube.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": playlist["id"],
                        "resourceId": {
                            "kind": "youtube#video",
                            "videoId": song,
                        },
                    }
                },
            )
            request.execute()
    except HttpError as e:
        print(f"An error occurred: {e}")


def get_unique_songs(main_playlist: Path, compare_playlist: Path) -> pd.DataFrame:
    """
    Compares two playlists and returns unique songs.

    Args:
        main_playlist (Path): Path to the main playlist file.
        compare_playlist (Path): Path to the playlist to compare against.

    Returns:
       path to the file containing the unique songs.
    """
    main_data = pd.read_csv(main_playlist)
    compare_data = pd.read_csv(compare_playlist)

    main_id = set(main_data["MediaId"])
    compare_id = set(compare_data["MediaId"])

    unique_id = compare_id - main_id
    unique = compare_data[compare_data["MediaId"].isin(unique_id)]

    return unique


def main():
    """
    Main function that creates the argument parser and processes the provided argument.
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
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

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the song names without processing the playlist.",
    )

    parser.add_argument(
        "--already_processed",
        type=str,
        help="Create playlist avoiding duplicates",
    )

    args = parser.parse_args()

    playlist_path = Path(args.csv_playlist)

    assert playlist_path.exists(), f"File `{playlist_path}` does not exist."
    assert playlist_path.is_file(), f"Path `{playlist_path}` is not a file."
    assert playlist_path.suffix == ".csv", f"File `{playlist_path}` is not a CSV file."

    playlist_name = args.playlist_name
    if playlist_name is None:
        playlist_name = get_youtube_playlist_name(playlist_path.name)

    if args.already_processed:
        compare_path = Path(args.already_processed)
        assert compare_path.exists(), f"File `{compare_path}` does not exist."
        assert (
            compare_path.suffix == ".csv"
        ), f"File `{compare_path}` is not a CSV file."

        unique_csv = get_unique_songs(playlist_path, compare_path)
        if args.dry_run:
            print("Dry run for unique songs:")
            unique_csv.apply(
                lambda row: print(
                    f"{row['Artists']} - "
                    + (
                        row["Title"][2:]
                        if row["Title"].startswith("e:")
                        else row["Title"]
                    )
                ),
                axis=1,
            )
            return
        process_playlist(unique_csv, playlist_name)
        return

    if args.dry_run:
        print(f"# {playlist_path.name}")
        print("# Songs:")
        pd.read_csv(playlist_path).apply(
            lambda row: print(
                f"{row['Artists']} - "
                + (row["Title"][2:] if row["Title"].startswith("e:") else row["Title"])
            ),
            axis=1,
        )
        return

    process_playlist(playlist_path, playlist_name)


if __name__ == "__main__":
    main()
