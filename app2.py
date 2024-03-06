from flask import Flask, render_template, request, session, redirect, url_for

# Import your Spotify script
import asyncio
from dotenv import load_dotenv
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import base64
import requests
from requests import post, get
import json

load_dotenv()

client_id = os.getenv("CLIENT_ID")
client_sec = os.getenv("CLIENT_SEC")

# Set in your Spotify Developer Dashboard
redirect_uri = os.getenv("REDIRECT_URI")
  




sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id, client_secret=client_sec, redirect_uri=redirect_uri, scope="user-library-read user-top-read playlist-modify-public playlist-modify-private user-read-private ", cache_path=".spotify_cache", show_dialog=True))

def create_playlist(playlist_name, is_public=True, description=''):
    try:
        playlist = sp.user_playlist_create(sp.me()['id'], playlist_name, public=is_public, description=description)
        return playlist['id']
    except spotipy.SpotifyException as e:
        # Handle the SpotifyException, and print or log the error message
        print(f"Error creating playlist: {e}")
        return None


# Function to add items to a playlist
def add_items_to_playlist(playlist_id, track_uris):
    sp.playlist_add_items(playlist_id, track_uris)

# Function to get recommendations for a track
def get_recommendations(track_name):
    results = sp.search(q=track_name, type='track')
    track_uri = results['tracks']['items'][0]['uri']
    recommendations = sp.recommendations(seed_tracks=[track_uri])['tracks']
    return recommendations

app = Flask(__name__)
app.secret_key = 'your_secret_key'
def add_recommendations(time_range, playlist_name, num_songs, playlist_id=None):
        # # Clear the cache before proceeding
        # cache_path = ".spotify_cache"
        # if os.path.exists(cache_path):
        #     os.remove(cache_path)
        if time_range == 'short_term':
            time = 'Last 4 Weeks'
        elif time_range == 'medium_term':
            time = 'Last 6 Months'
        else:
            time = 'All Time'

        playlist_id = create_playlist(playlist_name, is_public=False, description=f'Playlist Created Based On Your Music Listened To From {time}')

        

        user_top_tracks = sp.current_user_top_tracks(limit=num_songs, time_range=time_range)
        
        track_info_list = []

        for track in user_top_tracks['items']:
            recommended_tracks = get_recommendations(track['name'])[:1]

            track_uris = [rec_track['uri'] for rec_track in recommended_tracks]
            add_items_to_playlist(playlist_id, track_uris)

            track_info_list.append({
                'top_track_name': track['name'],
                'top_track_artist': track['artists'][0]['name'],
                'recommended_track_name': recommended_tracks[0]['name'],
                'recommended_track_artist': recommended_tracks[0]['artists'][0]['name']
            })

        return render_template(f'{time_range}.html', track_info_list=track_info_list)
    

def authenticated():
    return 'access_token' in session and 'user_id' in session

def get_current_tracks(playlist_id):
    # Check if playlist_id is available
    if not playlist_id:
        print("Error: Playlist ID is missing.")
        return []

    # Make the API request to get the current tracks in the playlist
    try:
        playlist_tracks = sp.playlist_tracks(playlist_id)
        return playlist_tracks['items']
    except spotipy.SpotifyException as e:
        print(f"Error getting current tracks: {str(e)}")
        return 
    
def remove_tracks_from_playlist(playlist_id, track_uris):
    # Check if playlist_id is available
    if not playlist_id:
        print("Error: Playlist ID is missing.")
        return False

    # Check if there are track_uris to remove
    if not track_uris:
        print("No tracks to remove.")
        return False

    try:
        # Make the API request to remove tracks from the playlist
        sp.playlist_remove_all_occurrences_of_items(playlist_id, track_uris)
        print("Tracks removed successfully.")
        return True
    except spotipy.SpotifyException as e:
        print(f"Error removing tracks from playlist: {str(e)}")
        return False


def clear_and_replace_playlist(playlist_id):
    # Check if playlist_id is available
    if not playlist_id:
        print("Error: Playlist ID is missing.")
        return

    # Get the current tracks in the playlist
    current_tracks = get_current_tracks(playlist_id)

    # Check if there are tracks to remove
    if not current_tracks:
        print("Playlist is already empty.")
        return

    # Create a list of track URIs to remove
    track_uris_to_remove = [track["track"]["uri"] for track in current_tracks]

    # Make the DELETE request to remove all occurrences of specified tracks
    if remove_tracks_from_playlist(playlist_id, track_uris_to_remove):
        print("Playlist cleared successfully.")
    else:
        print("Error clearing playlist.")

# New route for login
@app.route("/login")
def login():
    # Clear the cache before proceeding
    cache_path = ".spotify_cache"
    if os.path.exists(cache_path):
        os.remove(cache_path)
        return render_template('login.html')
    # Redirect the user to the Spotify login page
    return redirect(sp.auth_manager.get_authorize_url())

# Callback route after the user authorizes the app on Spotify
@app.route('/callback')
def callback():
    code = request.args['code']
    token_info = sp.auth_manager.get_access_token(code)

    # Store relevant information in the session
    session['access_token'] = token_info['access_token']
    session['user_id'] = sp.me()['id']

    # Redirect to the main page or dashboard
    return redirect(url_for('home'))


# Route for the main page
@app.route("/", methods=['GET', 'POST'])
def home():
    
    if not ('access_token' in session and 'user_id' in session):
        # Redirect to the login page if not authenticated
        return render_template('login.html')

    # print(client_id)
    # print(client_sec)
    # print(redirect_uri)

    if request.method == 'POST':
        playlist_name = request.form['playlist_name']
        num_songs = request.form['num_songs']

        # Retrieve the value of the clicked button
        time_range = request.form.get('time_range')

        if not playlist_name or not num_songs or not time_range:
            return render_template('home.html', error='Please fill in all fields.')

        try:
            num_songs = int(num_songs)
            if num_songs <= 0:
                raise ValueError("Number of songs must be a positive integer.")
        except ValueError:
            return render_template('home.html', error='Please enter a valid number of songs.')

        # Store the playlist_name in the session
        session['playlist_name'] = playlist_name
        session['num_songs'] = num_songs

        # Redirect to the appropriate route based on the button clicked
        if time_range == 'month':
            return redirect(url_for('last_6_months'))
        elif time_range == 'week':
            return redirect(url_for('last_4_weeks'))
        elif time_range == 'year':
            return redirect(url_for('all_time'))

    return render_template('home.html')




@app.route('/last_4_weeks', methods=['GET', 'POST'])
def last_4_weeks():
    # Retrieve playlist_name and num_songs from the session
    playlist_name = session.get('playlist_name')
    num_songs = session.get('num_songs')

    # Check if the form was submitted (POST request)
    if request.method == 'POST':
        # Handle the clear playlist button click here
        button_id = request.form.get('button_id')
        if button_id == 'clearButton':
            playlist_id = session.get("playlist_id")
            print(playlist_id)
            clear_and_replace_playlist(playlist_id)
            return add_recommendations('short_term', playlist_name, num_songs, playlist_id)




    # Call add_recommendations with the retrieved values
    return add_recommendations('short_term', playlist_name, num_songs)


@app.route('/last_6_months', methods=['GET', 'POST'])
def last_6_months():
    # Retrieve playlist_name and num_songs from the session
    playlist_name = session.get('playlist_name')
    num_songs = session.get('num_songs')

    if request.method == 'POST':
        # Handle the clear playlist button click here
        button_id = request.form.get('button_id')
        if button_id == 'clearButton':
            playlist_id = session.get("playlist_id")
            print(playlist_id)
            clear_and_replace_playlist(playlist_id)
            return add_recommendations('medium_term', playlist_name, num_songs, playlist_id)

    # Call add_recommendations with the retrieved values
    return add_recommendations('medium_term', playlist_name, num_songs)

@app.route('/all_time', methods=['GET', 'POST'])
def all_time():
    # Retrieve playlist_name and num_songs from the session
    playlist_name = session.get('playlist_name')
    num_songs = session.get('num_songs')

    if request.method == 'POST':
        # Handle the clear playlist button click here
        button_id = request.form.get('button_id')
        if button_id == 'clearButton':
            playlist_id = session.get("playlist_id")
            print(playlist_id)
            clear_and_replace_playlist(playlist_id)
            return add_recommendations('long_term', playlist_name, num_songs, playlist_id)

    # Call add_recommendations with the retrieved values
    return add_recommendations('long_term', playlist_name, num_songs)

if __name__ == "__main__":
    app.run(debug=True)
    
