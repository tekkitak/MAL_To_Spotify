from flask import Flask, render_template, redirect, url_for, request, session
from flask_session import Session
from urllib.parse import urlencode
import requests as rq
from os import getenv
import json
from datetime import datetime, timedelta
from helper_functions import exec_request, refresh_auth, encode_base64

from oauth2 import OAuth2, MalOAuth2Builder

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SECRET_KEY'] = getenv('FLASK_SECRET_KEY')
Session(app)


@app.route('/ajaxTest')
def ajaxTest():
    outJson = [
        {
            'title': 'Anime',
            'op_title': 'Opening name',
            'op_uri': 'spotify:link:idk'
        },
        {
            'title': 'Anime',
            'op_title': 'Opening name1',
            'op_uri': 'spotify:link:idk1'
        },
        {
            'title': 'Anime2',
            'op_title': 'Opening name2',
            'op_uri': 'spotify:link:idk2'
        },
        {
            'title': 'Anime3',
            'op_title': 'Opening name3',
            'op_uri': 'spotify:album:7JruDbtqHdtkxzIXBf6gjO'
        },
    ]
    return json.dumps(outJson)

@app.route('/')
def index():
    # session.clear()
    if session.get('spotify_access_token', False) != False:
        if session['token_expiration_time'] < datetime.now():
            refresh_auth()

    return render_template('index.j2', Spotify_OAuth_url=url_for('spotifyAuth'), Spotify_CreatePlaylist_url=url_for('create_spotify_playlist'), MAL_OAuth_url=url_for('malAuth'))



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






@app.route('/spotify/createPlaylist')
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

@app.route('/spotify/getSongUri/<string:name>/<string:artist>')
def get_song_uri(name = None, artist = None):
    url = "https://api.spotify.com/v1/search"
    querystring = {
        "q":f"track:{name} artist:{artist}",
        "type":"track",
        "limit":"1"
        }
    headers = {
        "Content-Type":"application/json",
        "Authorization":session['spotify_token_type'] + ' ' + session['spotify_access_token']
        }
    response = exec_request(url, headers=headers, params=querystring, method='GET')
    if response.status_code == 401:
        session['spotify_access_token'] = False
        return redirect(url_for('index'))
    return response.json()['tracks']['items'][0]['uri'] if response.status_code == 200 else False
    
    


@app.route('/auth/mal')
def malAuth(): 
    if session.get('mal_oauth', None) == None:
        session['mal_oauth'] = MalOAuth2Builder(getenv('MAL_ID'), 
                                                getenv('MAL_SECRET'), 
                                                "http://localhost:5000/auth/mal")
        return redirect(session['mal_oauth'].get_auth_url())

    if request.args.get('code', None) == None:
        return redirect(session['mal_oauth'].get_auth_url())
    
    session['mal_oauth'].token_from_code(request.args.get('code'))
    return redirect(url_for('index'))

@app.route('/mal/animeOpList')
def malAnimeOpList():
    op_list = []
    anime_list = []

    # Mal OAuth2
    OAuth = session.get("mal_oauth", None)
    if OAuth == None:
        return redirect("malAuth")
    
    # Gets users anime list
    url = "https://api.myanimelist.net/v2/users/@me/animelist"
    params={'fields': 'list_status', "limit": 25, "offset": 0}
    while True:
        ret = rq.get(url, params, auth=OAuth).json()

        if ret.get("error", None) != None:
            raise Exception("animelist", ret["error"])

        anime_list += ret["data"]

        if ret["paging"].get("next", None) == None:
            break
        params["offset"] += 25

    # We define a cache to avoid making too many requests to the API    
    if session.get("mal_anime_cache", None) == None:
        session["mal_anime_cache"] = []
    # We loop through the anime list and get the opening themes into op_list
    for anime in anime_list:
        if(anime['list_status']['status'] == "dropped" or 
           anime['list_status']['status'] == "plan_to_watch"):
            print("skipping anime " + anime["node"]["title"])
            continue

        if(request.args.get("completed_only", "true") == "true" and
           anime["list_status"]["status"] != "completed"):
            print("skipping anime " + anime["node"]["title"])
            continue
        
        if anime["node"]["title"] in [x["title"] for x in session["mal_anime_cache"]]:
            i = 0
            while anime["node"]["title"] != session["mal_anime_cache"][i]["title"]:
                i += 1
            op_list.append(session["mal_anime_cache"][i])
            continue

        anime_data = {"title": anime["node"]["title"], "op": []}
        url = f"https://api.myanimelist.net/v2/anime/{anime['node']['id']}"
        ret = rq.get(url, params={"fields": "opening_themes"}, auth=OAuth).json()
        if ret.get("error", None) != None:
            raise Exception("animedetails", ret["error"])

        anime_data["op"] = [x["text"] for x in ret.get("opening_themes", [])]
        
        op_list.append(anime_data)
        session["mal_anime_cache"].append(anime_data)
    return json.dumps(op_list)



app.route('/spotify/processMalList', methods=['POST'])
def process_mal_list():
    songs = request.form.get('openings')
    songs = json.loads(songs)
    uris = []
    for song in songs:
        uris += get_song_uri(song['name'], song['artist'])
    return uris