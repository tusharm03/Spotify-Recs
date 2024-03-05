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
import concurrent.futures

load_dotenv()

client_id = os.getenv("CLIENT_ID")
client_sec = os.getenv("CLIENT_SEC")

redirect_uri = os.getenv("REDIRECT_URI")  # Set in your Spotify Developer Dashboard




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

def process_track(track, playlist_id, time_range, track_info_list):
    recommended_tracks = get_recommendations(track['name'])[:1]
    track_uris = [rec_track['uri'] for rec_track in recommended_tracks]
    add_items_to_playlist(playlist_id, track_uris)

    track_info_list.append({
        'top_track_name': track['name'],
        'top_track_artist': track['artists'][0]['name'],
        'recommended_track_name': recommended_tracks[0]['name'],
        'recommended_track_artist': recommended_tracks[0]['artists'][0]['name']
    })

app = Flask(__name__)
app.secret_key = 'your_secret_key'

def add_recommendations(time_range, playlist_name, num_songs, batch_size=10):
    # Clear the cache before proceeding
    # cache_path = ".spotify_cache"
    # if os.path.exists(cache_path):
    #     os.remove(cache_path)

    if time_range == 'short_term':
        time = 'Last 4 Weeks'
        playlist_id = create_playlist(playlist_name, is_public=False, description=f'Playlist Created Based On Your Music Listened To From The {time}')
    elif time_range == 'medium_term':
        time = 'Last 6 Months'
        playlist_id = create_playlist(playlist_name, is_public=False, description=f'Playlist Created Based On Your Music Listened To From The {time}')
    elif time_range == 'long_term':
        time = 'All Time'
        playlist_id = create_playlist(playlist_name, is_public=False, description=f'Playlist Created Based On Your Music From {time}')

    # Render the loading page

    user_top_tracks = sp.current_user_top_tracks(limit=num_songs, time_range=time_range)

    track_info_list = []

    for i in range(0, num_songs, batch_size):
        batch_of_tracks = user_top_tracks['items'][i:i + batch_size]
        recommended_tracks_batch = []

        for track in batch_of_tracks:
            recommended_tracks = get_recommendations(track['name'])[:1]
            recommended_tracks_batch.extend(recommended_tracks)

            track_uris = [rec_track['uri'] for rec_track in recommended_tracks]
            add_items_to_playlist(playlist_id, track_uris)

            track_info_list.append({
                'top_track_name': track['name'],
                'top_track_artist': track['artists'][0]['name'],
                'recommended_track_name': recommended_tracks[0]['name'],
                'recommended_track_artist': recommended_tracks[0]['artists'][0]['name']
            })

        if len(track_info_list) != i + batch_size:
            loading_page = f'{time_range}_loading.html'
            return render_template(loading_page)

    if time_range == 'short_term':
        # Render the short_term.html template and pass track_info_list to it
        return render_template('short_term.html', track_info_list=track_info_list)
    elif time_range == 'medium_term':
        return render_template('medium_term.html', track_info_list=track_info_list)
    elif time_range == 'long_term':
        return render_template('long_term.html', track_info_list=track_info_list)

    return render_template(f'{time_range}.html', track_info_list=track_info_list)

# def add_recommendations(time_range, playlist_name, num_songs):
#     # Clear the cache before proceeding
#     # cache_path = ".spotify_cache"
#     # if os.path.exists(cache_path):
#     #     os.remove(cache_path)
    
#     if time_range == 'short_term':
#         time = 'Last 4 Weeks'
#         playlist_id = create_playlist(playlist_name, is_public=False, description=f'Playlist Created Based On Your Music Listened To From The {time}')
#     elif time_range == 'medium_term':
#         time = 'Last 6 Months'
#         playlist_id = create_playlist(playlist_name, is_public=False, description=f'Playlist Created Based On Your Music Listened To From The {time}')
#     elif time_range == 'long_term':
#         time = 'All Time'
#         playlist_id = create_playlist(playlist_name, is_public=False, description=f'Playlist Created Based On Your Music From {time}')

#     # Render the loading page


#     user_top_tracks = sp.current_user_top_tracks(limit=num_songs, time_range=time_range)
    
#     track_info_list = []

#     for track in user_top_tracks['items']:
#         recommended_tracks = get_recommendations(track['name'])[:1]

#         track_uris = [rec_track['uri'] for rec_track in recommended_tracks]
#         add_items_to_playlist(playlist_id, track_uris)

#         track_info_list.append({
#             'top_track_name': track['name'],
#             'top_track_artist': track['artists'][0]['name'],
#             'recommended_track_name': recommended_tracks[0]['name'],
#             'recommended_track_artist': recommended_tracks[0]['artists'][0]['name']
#         })

#     while len(track_info_list) != num_songs:
#             loading_page = f'{time_range}_loading.html'
#             return render_template(loading_page)

#     if time_range == 'short_term':
#         # Render the short_term.html template and pass track_info_list to it
#         return render_template('short_term.html', track_info_list=track_info_list) 
#     elif time_range == 'medium_term':
#         return render_template('medium_term.html', track_info_list=track_info_list) 
#     elif time_range == 'long_term':
#         return render_template('long_term.html', track_info_list=track_info_list) 

#     return render_template(f'{time_range}.html', track_info_list=track_info_list)

    





@app.route("/", methods=['GET', 'POST'])
def home():
    print(client_id)
    print(client_sec)
    print(redirect_uri)
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

@app.route('/callback')
def callback():
    print('Callback route accessed')
    print('Authorization code:', request.args['code'])
    sp.auth_manager.get_access_token(request.args['code'], as_dict=False)
    return redirect(url_for('home'))



@app.route('/last_4_weeks')
def last_4_weeks():
    # Retrieve playlist_name and num_songs from the session
    playlist_name = session.get('playlist_name')
    num_songs = session.get('num_songs')

    # Call add_recommendations with the retrieved values
    return add_recommendations('short_term', playlist_name, num_songs)


@app.route('/last_6_months')
def last_6_months():
    # Retrieve playlist_name and num_songs from the session
    playlist_name = session.get('playlist_name')
    num_songs = session.get('num_songs')

    # Call add_recommendations with the retrieved values
    return add_recommendations('medium_term', playlist_name, num_songs)

@app.route('/all_time')
def all_time():
    # Retrieve playlist_name and num_songs from the session
    playlist_name = session.get('playlist_name')
    num_songs = session.get('num_songs')

    # Call add_recommendations with the retrieved values
    return add_recommendations('long_term', playlist_name, num_songs)

if __name__ == "__main__":
    app.run(debug=True)
    
