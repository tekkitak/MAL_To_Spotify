from flask import Flask, render_template, redirect, url_for, request, session
from flask_session import Session
from urllib.parse import urlencode
import requests as rq
from os import getenv
from base64 import b64encode as b64en
import json


app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SECRET_KEY'] = getenv('FLASK_SECRET_KEY')
Session(app)




@app.route('/')
def index():
    return render_template('index.html', Spotify_OAuth_url=url_for('spotifyAuth'), Spotify_CreatePlaylist_url=url_for('create_spotify_playlist'))



@app.route('/auth/spotify')
def spotifyAuth():
    if request.args.get('code', None) == None:
        url = "https://accounts.spotify.com/authorize"
        querystring = {
            "client_id":getenv('SPOT_ID', None),
            "response_type":"code",
            "redirect_uri":"http://localhost:5000/auth/spotify",
            "scope":"playlist-modify-private playlist-modify-public user-library-read user-library-modify user-read-private"
            }
        redirectUrl = url + '?' + urlencode(querystring)
        return redirect(redirectUrl)
    
    code = request.args.get('code')
    out = spotify_get_OAuth(code)
    session['spotify_access_token'] = out['access_token']
    session['spotify_refresh_token'] = out['refresh_token']
    session['spotify_token_type'] = out['token_type']

    print(session['spotify_access_token'])
    print(session['spotify_refresh_token'])
    print(session['spotify_token_type'])
    
    # return out
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
    req = rq.post(url, data=body, headers=headers)

    # if req.json().get('error', None) != None:
    #     raise Exception(req.json()['error'])
    return req.json()



def encode_base64(string):
    return b64en(string.encode('ascii')).decode('ascii')


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
    response = rq.post(url, data=data, headers=headers)
    print('create_spotify_playlist')
    print(response.text)
    return redirect(url_for('index'))


def get_spotify_user_profile():
    url = "https://api.spotify.com/v1/me"
    headers = {
        "Content-Type":"application/json",
        "Authorization":session['spotify_token_type'] + ' ' + session['spotify_access_token']
        }
    response = rq.get(url, headers=headers)
    print('get_spotify_user_profile')
    print(response.text)
    return response.json()



def playlist_add_songs(uris):
    headers = {
        "Content-Type":"application/json",
        "Authorization":session['spotify_token_type'] + ' ' + session['spotify_access_token']
        }
    data = {
        "uris": uris,
        "position": 0
        }
    response = rq.post(json.dumps(data), headers=headers)
    print(response.text)
    return response.json()


def get_song_uri(name):
    #TODO: get song uri from spotify
    pass


def process_mal_list(songs):
    uris = []
    for song in songs:
        uris += get_song_uri(song)
    return uris