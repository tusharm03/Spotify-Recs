from dotenv import load_dotenv
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import base64
import requests
from requests import post, get
import json
import time

load_dotenv()

client_id = os.getenv("CLIENT_ID")
client_sec = os.getenv("CLIENT_SEC")
redirect_uri = os.getenv("REDIRECT_URI")

def get_token():
    auth_string = client_id + ":" + client_sec
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

    url = "https://accounts.spotify.com/api/token"

    headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    result = post(url, headers=headers, data=data)
    json_result = json.loads(result.content)
    token = json_result["access_token"]
    return token

def get_auth_header(token):
    return {"Authorization": "Bearer " + token}

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id, client_secret=client_sec, redirect_uri=redirect_uri, scope="playlist-modify-private playlist-modify-public user-library-read user-top-read", cache_path=".spotify_cache", show_dialog=True))

def get_recommendations(track_name):
    try:
        # Search for the given track name
        results = sp.search(q=track_name, type="track")

        # Check if there are any tracks in the search results
        if 'tracks' in results and 'items' in results['tracks'] and results['tracks']['items']:
            # Extract the URI of the first track
            track_uri = results['tracks']['items'][0]['uri']
            print("Track URI:", track_uri)

            # Get recommendations based on the seed track
            recommendations = sp.recommendations(seed_tracks=[track_uri])['tracks']

            # Check if there are any recommended tracks
            if recommendations:
                return recommendations
            else:
                print("No recommendations found.")
                return None
        else:
            print("No tracks found in the search results.")
            return None

    except Exception as e:
        print(f"An error occurred: {e}")
        return None


# Create a new playlist
playlist_name = "Recommended Tracks Playlist"
user_id = sp.me()['id']
playlist = sp.user_playlist_create(user=user_id, name=playlist_name, public=True)

# Get and add recommendations to the playlist
for track in sp.current_user_top_tracks(limit=10, time_range='long_term')['items']:
    track_name = track['name']
    print(track_name)
    recommended_tracks = get_recommendations(track_name)[:2]

    for rec_track in recommended_tracks:
        sp.playlist_add_items(playlist['id'], items=[rec_track['uri']])

    print(f"Added recommendations for '{track_name}' to the playlist.")

print(f"\nPlaylist '{playlist_name}' created successfully!")

cache_path = ".spotify_cache"
if os.path.exists(cache_path):
    os.remove(cache_path)











































# def get_user_top_tracks(token):
#     url = "https://api.spotify.com/v1/me/top/artists"
#     headers = get_auth_header(token)
#     params = {
#         'time_range': 'medium_term',  # You can change this if needed
#         'limit': 20,
#         'offset': 0
#     }

#     response = requests.get(url, headers=headers, params=params)

#     if response.status_code == 200:
#         # Successful response
#         return response.json()
#     else:
#         # Handle error
#         print(f"Error: {response.status_code}, {response.text}")
#         return None
    
# def search_for_artist(token, artist_name):
#     url = "https://api.spotify.com/v1/search"
#     headers = get_auth_header(token)
#     query = f"?q={artist_name}&type=artist&limit=1"

#     query_url = url + query
#     result = get(query_url, headers=headers)
#     json_result = json.loads(result.content)["artists"]["items"]
#     if len(json_result) == 0:
#         print("No Artist Found")
#         return None
#     return json_result[0]


# def get_songs_by_artist(token,artist_id):
#     url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks?country=US"
#     headers = get_auth_header(token)
#     result = get(url,headers=headers)
#     json_result = json.loads(result.content)["tracks"]
#     return json_result





# token = get_token()

# result = search_for_artist(token,"Drake")
# artist_id = result["id"]
# songs = get_songs_by_artist(token,artist_id)

# for idx,song in enumerate(songs):
#     print(f"{idx + 1}. {song['name']}")





































































# def get_spotipy_object():
#     return spotipy.Spotify(auth_manager=SpotifyOAuth(
#         client_id=client_id,
#         client_secret=client_sec,
#         redirect_uri=redirect_uri,
#         scope=['user-read-private', 'playlist-modify-private', 'playlist-modify-public', 'user-top-read', 'user-read-email']
#     ))

# sp = get_spotipy_object()

# def get_user_id():

#     user_profile = sp.current_user()
#     user_id = user_profile.get('id', 'N/A')

#     return user_id

# def create_playlist(sp, user_id, playlist_name, is_public=True, is_collaborative=False, description=''):
#     data = {
#         'name': playlist_name,
#         'public': is_public,
#         'collaborative': is_collaborative,
#         'description': description
#     }
#     response = sp.user_playlist_create(user_id, **data)

#     if 'id' in response:
#         return response['id']
#     else:
#         print(f'Error creating playlist: {response}')
#         return None

# def add_top_tracks_to_playlist(sp, playlist_id, top_tracks, limit=10):
#     track_uris = [track['uri'] for track in top_tracks['items'][:limit]]
#     sp.playlist_add_items(playlist_id, track_uris)

# def get_recommendations(sp, seed_tracks, limit=10):
#     seed_track_uris = [f"spotify:track:{track_id}" for track_id in seed_tracks]

#     try:
#         recommendations = sp.recommendations(seed_tracks=seed_track_uris, limit=limit)
#     except spotipy.SpotifyException as e:
#         print(f"Exception occurred: {e}")
#         recommendations = None

#     if recommendations and 'tracks' in recommendations:
#         return [track['uri'] for track in recommendations['tracks']]
#     else:
#         print("No recommendations due to an error.")
#         return []

# def main():
#     sp = get_spotipy_object()
#     user_id = get_user_id(sp)

#     playlist_name = 'Your Coolest Playlist'
#     is_public = True
#     is_collaborative = False
#     description = 'Playlist created using the Spotify Web API'

#     top_tracks = sp.current_user_top_tracks(limit=10)
#     playlist_id = create_playlist(sp, user_id, playlist_name, is_public, is_collaborative, description)

#     if playlist_id:
#         print(f'Playlist "{playlist_name}" created successfully!')
#         print(f'Playlist ID: {playlist_id}')

#         add_top_tracks_to_playlist(sp, playlist_id, top_tracks)

#         # Introduce a delay to ensure top tracks are added before proceeding
#         time.sleep(5)

#         seed_tracks = [track['id'] for track in top_tracks['items']]
#         recommended_tracks = get_recommendations(sp, seed_tracks)

#         sp.playlist_add_items(playlist_id, recommended_tracks)
#         print('Recommended tracks added to the playlist!')

# if __name__ == "__main__":
#     main()
