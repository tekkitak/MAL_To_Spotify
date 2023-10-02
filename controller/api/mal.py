from os import getenv
from time import time
from datetime import datetime
import json
import requests as rq
import requests as rq
from flask import Blueprint, redirect, url_for, request, session
from oauth2 import MalOAuth2Builder
from flask import redirect, url_for, request, session
from oauth2 import OAuth2
from database import db, Anime
from helper_functions import parseOP
from controller.api.spotify import get_song_uri

mal = Blueprint('mal', __name__, 
                template_folder='templates/api/mal',
                url_prefix='/mal')

@mal.route('/auth')
def malAuth(): 
    if session.get('mal_oauth', None) is None:
        session['mal_oauth'] = MalOAuth2Builder(getenv('MAL_ID'), 
                                                getenv('MAL_SECRET'), 
                                                "http://localhost:5000/api/mal/auth")
        return redirect(session['mal_oauth'].get_auth_url())

    if request.args.get('code', None) is None:
        return redirect(session['mal_oauth'].get_auth_url())

    session['mal_oauth'].token_from_code(request.args.get('code'))
    return redirect(url_for('index'))

@mal.route('/animeOpList')
def malAnimeOpList():
    op_list = []
    anime_list = []

    # Mal OAuth2
    Oauth: None|OAuth2 = session.get("mal_oauth", None)
    if Oauth is None:
        return redirect("malAuth")

    # Gets users anime list
    url = "https://api.myanimelist.net/v2/users/@me/animelist"
    params: dict[str, str|int] = {
        'fields': 'list_status',
        "limit": 25,
        "offset": 0
    }
    while True:
        ret = rq.get(url, params, auth=Oauth, timeout=150).json()

        if ret.get("error", None) is not None:
            raise Exception("animelist", ret["error"])

        anime_list += ret["data"]

        if ret["paging"].get("next", None) is None:
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
        ret = rq.get(url, params={"fields": "opening_themes"}, auth=Oauth, timeout=500).json()
        if ret.get("error", None) is not None:
            raise Exception("animedetails", ret["error"])


        try:
            anim = Anime.query.filter_by(anime_title=anime["node"]["title"]).one_or_none()
            if anim is None:
                openings = [parseOP(x["text"]) for x in ret.get("opening_themes", [])]
                for op in openings:
                    if op.spotify_uri is None:
                        try:
                            op.spotify_uri = get_song_uri(op.opening_title, op.artist.name)
                        except Exception as error:
                            print("Error: 404")
                            print(anime["node"]["title"])
                            print(f"{op=}")
                            raise error

                anim = Anime(anime_title=anime["node"]["title"], openings=openings)
            else:
                anim.openings = [parseOP(x["text"]) for x in ret.get("opening_themes", [])]

            db.session.add(anim)
            db.session.commit()
        except Exception as error:
            print(anime["node"]["title"]) 
            print(ret.get("opening_themes", []))
            db.session.rollback()
            raise error


        for op in anim.openings:
            anime_data = {
                    "title": anime["node"]["title"],
                    "op_title": op.opening_title,
                    "op_artist": op.artist.name,
                    "op_uri": op.spotify_uri
            }

            op_list.append(anime_data)


    return json.dumps(op_list)
