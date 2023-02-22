from flask import Flask, render_template, redirect, url_for, request, session
from flask_session import Session
from urllib.parse import urlencode
import requests as rq
from os import getenv
import json
from datetime import datetime, timedelta
from helper_functions import exec_request, refresh_auth, encode_base64


app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SECRET_KEY'] = getenv('FLASK_SECRET_KEY')
Session(app)




@app.route('/')
def index():
    # session.clear()
    # session['token_expiration_time'] = datetime.now() - timedelta(seconds=1)
    if session.get('spotify_access_token', False) != False:
        if session['token_expiration_time'] < datetime.now():
            refresh_auth()
    print("expiration time:" + (session['token_expiration_time'].strftime("%m/%d/%Y, %H:%M:%S")) if 'token_expiration_time' in session else "None")
    return render_template('index.html', Spotify_OAuth_url=url_for('spotifyAuth'), Spotify_CreatePlaylist_url=url_for('create_spotify_playlist'))



@app.route('/auth/spotify')
def spotifyAuth():
    if request.args.get('code', None) == None:
        url = "https://accounts.spotify.com/authorize"
        querystring = {
            "client_id":getenv('SPOT_ID', None),
            "response_type":"code",
            "redirect_uri":"http://localhost:5000/auth/spotify",
            "scope":"playlist-modify-private playlist-modify-public user-library-read user-library-modify"
            }
        redirectUrl = url + '?' + urlencode(querystring)
        return redirect(redirectUrl)
    
    code = request.args.get('code')
    out = spotify_get_OAuth(code)
    session['spotify_access_token'] = out['access_token']
    session['spotify_refresh_token'] = out['refresh_token']
    session['spotify_token_type'] = out['token_type']
    session['token_expiration_time'] = datetime.now() + timedelta(seconds=out['expires_in'])
    session['spotify_refresh_token'] = out['refresh_token']
    
    return redirect(url_for('index'))




def spotify_get_OAuth(code):
    url = "https://accounts.spotify.com/api/token"
    body = {
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': 'http://localhost:5000/auth/spotify',
        'client_id': getenv('SPOT_ID'),
        'client_secret': getenv('SPOT_SECRET'),
    }
    headers = {
        'Authorization': 'Basic ' + encode_base64(getenv('SPOT_ID') + ':' + getenv('SPOT_SECRET')),
        'Content-type': 'application/x-www-form-urlencoded'
    }
    req = exec_request(url, headers=headers, data=body, method='POST', auth=False)

    print('spotify_get_OAuth')
    print(req.text)
    if req.status_code == 401:
        return redirect(url_for('index')) 
    return req.json()






@app.route('/createPlaylist')
def create_spotify_playlist():
    user_profile = get_spotify_user_profile()
    user_id = user_profile['id']
    url = f"https://api.spotify.com/v1/users/{user_id}/playlists"
    data = '''{
        "name":"MyAnimeList openings",
        "description":"Openings from my MyAnimeList",
        "public":"false"
        }'''
    headers = {
        "Content-Type":"application/json",
        "Authorization":session['spotify_token_type'] + ' ' + session['spotify_access_token']
        }
    response = exec_request(url, headers=headers, data=data, method='POST')
    return redirect(url_for('index'))


def get_spotify_user_profile():
    url = "https://api.spotify.com/v1/me"
    headers = {
        "Content-Type":"application/json",
        "Authorization":session['spotify_token_type'] + ' ' + session['spotify_access_token']
        }
    response = exec_request(url, headers=headers, method='GET')

    if response.status_code == 401:
        session['spotify_access_token'] = False
        return redirect(url_for('index'))
    return response.json() if response.status_code == 200 else False



def playlist_add_songs(uris, playlist_id):
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    headers = {
        "Content-Type":"application/json",
        "Authorization":session['spotify_token_type'] + ' ' + session['spotify_access_token']
        }
    data = {
        "uris": uris,
        "position": 0
        }
    response = exec_request(url, headers=headers, data=data, method='POST')
    return response.json()


def get_song_uri(name):
    #TODO: get song uri from spotify
    pass


def process_mal_list(songs):
    uris = []
    for song in songs:
        uris += get_song_uri(song)
    return uris