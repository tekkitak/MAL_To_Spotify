from flask import Flask, render_template, redirect, url_for, request, session
from time import time
from datetime import datetime
from flask_session import Session
from urllib.parse import urlencode
import requests as rq
from os import getenv
import json
from datetime import datetime, timedelta
import re 
from helper_functions import exec_request, refresh_auth, encode_base64, parseOP
from typing import cast, Any, Union
from database import db, Anime, Opening, Artist
import re
from actions import register_commands

from oauth2 import OAuth2, MalOAuth2Builder

app = Flask(__name__)
register_commands(app)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SECRET_KEY'] = getenv('FLASK_SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = getenv('DATABASE_URL')
print(app.config['SQLALCHEMY_DATABASE_URI'])
db.init_app(app)
Session(app)

with app.app_context():
    db.create_all()


@app.route('/')
def index():
    # session.clear()
    playlists = []
    if session.get('spotify_access_token', False) != False:
        if session['token_expiration_time'] < datetime.now():
            refresh_auth()
        playlists = spotify_playlists()['items']
    return render_template('index.j2', Spotify_OAuth_url=url_for('spotifyAuth'), MAL_OAuth_url=url_for('malAuth'), playlists=playlists)



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
    if out == None:
        return redirect(url_for('index'))
    session['spotify_access_token'] = out['access_token']
    session['spotify_token_type'] = out['token_type']
    session['token_expiration_time'] = datetime.now() + timedelta(seconds=out['expires_in'])
    session['spotify_refresh_token'] = out['refresh_token']
    
    return redirect(url_for('index'))




def spotify_get_OAuth(code) -> Union[dict,Any]:
    assert getenv('SPOT_ID') != None and getenv('SPOT_SECRET') != None, 'SPOT_ID or SPOT_SECRET not set'
    spot_id:str     = cast(str,getenv('SPOT_ID'))
    spot_secret:str = cast(str,getenv('SPOT_SECRET'))
    
    url = "https://accounts.spotify.com/api/token"
    body = {
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': 'http://localhost:5000/auth/spotify',
        'client_id': spot_id,
        'client_secret': spot_secret,
    }
    headers = {
        'Authorization': 'Basic ' + encode_base64(spot_id + ':' + spot_secret),
        'Content-type': 'application/x-www-form-urlencoded'
    }
    req = cast(rq.Response, exec_request(url, headers=headers, data=body, method='POST', auth=False))

    return req.json()






@app.route('/spotify/createPlaylist/<string:name>')
def create_spotify_playlist( name = 'MyAnimeList openings' ):
    print('Creating playlist: ' + name)
    user_profile = get_spotify_user_profile()
    user_id = user_profile['id']
    url = f"https://api.spotify.com/v1/users/{user_id}/playlists"
    data = '''{
        "name":"''' + name + '''",
        "description":"Openings from my MyAnimeList",
        "public":"false"
        }'''
    headers = {
        "Content-Type":"application/json",
        "Authorization":session['spotify_token_type'] + ' ' + session['spotify_access_token']
        }
    response = cast(rq.Response,exec_request(url, headers=headers, data=data, method='POST'))
    print(response.text)
    return response.json()['id']


def get_spotify_user_profile() -> Union[dict,Any]:
    url = "https://api.spotify.com/v1/me"
    headers = {
        "Content-Type":"application/json",
        "Authorization":session['spotify_token_type'] + ' ' + session['spotify_access_token']
        }
    response = cast(rq.Response,exec_request(url, headers=headers, method='GET'))

    if response.status_code != 200: raise Exception('Error getting user profile')
    return response.json() 


@app.route('/spotify/addSongs/<string:playlist_id>/<string:uris>')
def playlist_add_songs(uris, playlist_id):
    uris = uris.split(',')
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    headers = {
        "Content-Type":"application/json",
        "Authorization":session['spotify_token_type'] + ' ' + session['spotify_access_token']
        }
    print (uris)
    data = {
        "uris": uris,
        "position": 0
        }
    
    response = exec_request(url, headers=headers, data=json.dumps(data), method='POST')
    return redirect(url_for('index'))

@app.route('/spotify/getSongUri/<string:name>/<string:artist>') # type: ignore
def get_song_uri(name = None, artist = None) -> Union[str,None]:
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
    response = cast(rq.Response, exec_request(url, headers=headers, params=querystring, method='GET'))

    if response.status_code != 200: raise Exception('Error getting song uri') 
    if response.json()['tracks']['total'] == 0: 
        querystring = {
            "q":f"track:{name}",
            "type":"track",
            "limit":"1"
        }

        response = cast(rq.Response, exec_request(url, headers=headers, params=querystring, method='GET'))
        if response.status_code != 200: raise Exception('Error getting song uri')
        if response.json()['tracks']['total'] == 0: return None
    return response.json()['tracks']['items'][0]['uri']
   
    
    

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

    anime_titles = [x["node"]["title"] for x in anime_list]
    anime_cache = Anime.query.where(Anime.anime_title.in_(anime_titles))
    # We loop through the anime list and get the opening themes into op_list
    for anime in anime_list:
        if(anime['list_status']['status'] == "dropped" or 
           anime['list_status']['status'] == "plan_to_watch"):
            if getenv("DEBUG") == "true": print("skipping anime " + anime["node"]["title"])
            continue

        if(request.args.get("completed_only", "true") == "true" and
           anime["list_status"]["status"] != "completed"):
            if getenv("DEBUG") == "true": print("skipping anime " + anime["node"]["title"])
            continue
        

        if anime["node"]["title"] in [x.anime_title for x in anime_cache]:
            out_str = "______________________________\n"
            out_str += f" >> {anime['node']['title']} <<\n"
            start = time()
            for cached in anime_cache:
                if cached.anime_title == anime["node"]["title"]:
                    for op in cached.openings:
                        if op.spotify_uri == None and op.spotify_last_check.timestamp()+86400 < time():
                            op.spotify_last_check = datetime.now()
                            out_str += "Hit song without uri\n"
                            out_str += f"{time()-start}s\n"
                            op.spotify_uri = get_song_uri(op.opening_title, op.artist.name)
                            db.session.commit()
                            

                        out_str += "Op list append\n"
                        out_str += f"{time()-start}s\n"
                        op_list.append({
                            "title": cached.anime_title,
                            "op_title": op.opening_title,
                            "op_artist": op.artist.name,
                            "op_uri": op.spotify_uri
                        })
            out_str += "Done\n"
            out_str += f"{time()-start}s\n______________________________"
            if time()-start > .2 and getenv("DEBUG") == "true":
                print(out_str)
            continue

        url = f"https://api.myanimelist.net/v2/anime/{anime['node']['id']}"
        ret = rq.get(url, params={"fields": "opening_themes"}, auth=OAuth).json()
        if ret.get("error", None) != None:
            raise Exception("animedetails", ret["error"])


        try:
            anim = Anime.query.filter_by(anime_title=anime["node"]["title"]).one_or_none()
            if anim == None:
                openings = [parseOP(x["text"]) for x in ret.get("opening_themes", [])]
                for op in openings:
                    if op.spotify_uri == None:
                        try:
                            op.spotify_uri = get_song_uri(op.opening_title, op.artist.name)
                        except Exception as e:
                            print("Error: 404")
                            print(anime["node"]["title"])
                            print(f"{op=}")
                            raise e

                anim = Anime(anime_title=anime["node"]["title"], openings=openings)
            else:
                anim.openings = [parseOP(x["text"]) for x in ret.get("opening_themes", [])]

            db.session.add(anim)
            db.session.commit()
        except Exception as e:
            print(anime["node"]["title"]) 
            print(ret.get("opening_themes", []))
            raise e
            db.session.rollback()


        for op in anim.openings:
            anime_data = {
                    "title": anime["node"]["title"],
                    "op_title": op.opening_title,
                    "op_artist": op.artist.name,
                    "op_uri": op.spotify_uri
            }
        
            op_list.append(anime_data)


    return json.dumps(op_list)

@app.route('/spotify/playlists')
def spotify_playlists():
    url = "https://api.spotify.com/v1/me/playlists"
    headers = {
        "Content-Type":"application/json",
        "Authorization":session['spotify_token_type'] + ' ' + session['spotify_access_token']
        }
    response = cast(rq.Response,exec_request(url, headers=headers, method='GET'))

    if response.status_code != 200: raise Exception('Error getting user playlists')
    return response.json()
