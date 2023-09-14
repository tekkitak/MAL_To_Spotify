from flask import Flask, render_template, redirect, url_for, request, session
from time import time
from datetime import datetime
from flask_session import Session # type: ignore -- package stub issue... 
import requests as rq
from os import getenv
import json
from datetime import datetime
from helper_functions import refresh_auth, parseOP
from database import db, Anime
from actions import register_commands

from controller.error import error
from controller.api import api
from oauth2 import MalOAuth2Builder

app = Flask(__name__)
register_commands(app)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SECRET_KEY'] = getenv('FLASK_SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = getenv('DATABASE_URL')
app.register_blueprint(error)
app.register_blueprint(api)
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

