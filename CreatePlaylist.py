"""
Step 1: Log Into Youtube
Step 2: Grab Our Liked Videos & Creating a Dictionary of Important Song Information
Step 3: Create A New Playlist
Step 4: Search For the Song
Step 5: Add this song into the new Spotify playlist
"""
import json
import os
import requests

from secrets import spotify_token, spotify_user_id
from exceptions import ResponseException
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import youtube_dl



class CreatePlaylist:

    def __init__(self):
        self.user_id = spotify_user_id
        self.spotify_token = spotify_token
        self.youtube_client = self.get_youtube_client()
        self.all_song_info = {}


    # Step 1
    def get_youtube_client(self):
        # copied from Youtube Data API
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        api_service_name = "youtube"
        api_version = "v3"
        client_secrets_file = "YOUR_CLIENT_SECRET_FILE.json"

        # get credentials and create and API client
        scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes)
        credentials = flow.run_console()

        # from the Youtube DATA API
        youtube_client = googleapiclient.discovery.build(api_service_name, api_version, credentials=credentials)

        return youtube_client


    # Step 2
    def get_liked_videos(self):
        request = self.youtube_client.videos().list(
            part="snippet,contentDetails,statistics",
            myRating="like"
        )
        response = request.execute()

        # collect each video and get important information using loops
        for item in response["items"]:
            video_title = item["snippet"]["title"]
            youtube_url = "https://www.youtube.com/watch?v={}".format(item["id"])

            # use youtube_dl to collect the song name & artist name
            video = youtube_dl.YoutubeDL({}).extract_info(youtube_url, download=False)
            song_name = video["track"]
            artist_name = video["artist"]

            # save all important info
            self.all_song_info[video_title] = {
                "youtube_url":youtube_url,
                "song_name":song_name,
                "artist_name":artist_name,

                # add the song's uri, easy to get song to put into playlist
                "spotify_uri":self.get_spotify_url(song_name, artist_name)
            }


    # Step 3
    def create_playlist(self):
        request_body = json.dumps({
            "name": "Youtube Study Playlist",
            "description": "All liked Youtube videos",
            "public":True
        })
        query = "https://api.spotify.com/v1/users/{}/playlists".format(self.user_id)
        response = requests.post(
            query,
            data = request_body,
            headers = {
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(self.spotify_token)
            }
        )
        response_json = response.json()

        #playlist id
        return response_json("id")

    # Step 4
    def get_spotify_url(self, song_name, artist):
        query = "https://api.spotify.com/v1/search?query=track%3A{}+artist%3A{}&type=track&offset=0&limit=20".format(
            song_name,
            artist
        )
        response = requests.get(
            query,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(self.spotify_token)
            }
        )
        response_json = response.json()
        songs = response_json["tracks"]["items"]

        # only use the first song
        uri = songs[0]["uri"]
        return uri

    # Step 5
    def add_song_to_playlist(self):
        # populate our songs dictionary
        self.get_liked_videos()

        # collect all of uri
        uris = []
        for song, info in self.all_song_info.items():
            uris.append(info["spotify_uri"])

        # create a new playlist
        playlist_id = self.create_playlist()

        # add all songs into new playlist
        request_data = json.dumps(uris)

        query = "https://api.spotify.com/v1/playlists/{}/tracks".format(playlist_id)

        response = requests.post(
            query,
            data=request_data,
            headers = {
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(self.spotify_token)
            }
        )
        response_json = response.json()
        return response_json
