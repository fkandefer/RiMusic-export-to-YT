# RiMusic-export-to-YT

## Generate own `client_secret.json`

1. [Create a Google Cloud project](https://console.cloud.google.com/projectcreate) (e.g. with `YouTube-importer` name)
2. [Turn on the YouTube Data API v3](https://console.cloud.google.com/marketplace/product/google/youtube.googleapis.com)
3. [Set up a "Create credentials" wizard](https://console.cloud.google.com/apis/credentials/wizard?api=youtube.googleapis.com)
    1. Select an API: YouTube Data v3
    2. What data will you be accessing? User data
    3. Provide app info (it doesn't really matter)
    4. Scopes: Save
    5. Application type: Desktop app
    6. Create
    7. Download `client_secret.json`
4. [Add your e-mail address as Test user](https://console.cloud.google.com/apis/credentials/consent)


## Tips:

You can use `--dry-run` mode to export playlist to Spotify with [spotlistr.com](https://www.spotlistr.com/search/textbox).
