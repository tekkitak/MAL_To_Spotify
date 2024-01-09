from os import getenv
from time import time
from typing import Optional, cast, Any
from datetime import datetime
import re
import json
import requests as rq
from flask import Blueprint, redirect, url_for, request, session
from flask import redirect, url_for, request, session
from model.oauth2 import MalOAuth2Builder, OAuth2
from model.database import db, Anime, Opening, Artist, Vote, Song
from controller.api.spotify import create_spotify_song 
from sqlalchemy.orm import Session as SQLSession

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
def malGenerateOPList():
    Oauth: Optional[OAuth2] = cast(Optional[OAuth2], session.get("mal_oauth", None))
    if Oauth is None:
        return redirect("malAuth")

    # output json
    json_out: list[dict[str, str]] = []

    # Get user anime list 
    anime_list = getAnimeList(Oauth)

    # Find openings from db, if fails find from api
    for anime_data in anime_list:
        anime_status: str = anime_data['status_data']['status'] # type: ignore
        anime_title: str = anime_data['title'] # type: ignore
        anime_id: int = int(anime_data['id']) # type: ignore

        comp_only: bool = request.args.get("completed_only", "true") == "true"
        if anime_status in ["dropped", "plan_to_watch"]:
            continue
        if comp_only and anime_status != "completed":
            continue

        cached: Anime = Anime.query.filter_by(title=anime_title).one_or_none() # type: ignore
        anime: Anime
        if cached is None:
            anime = Anime(title=anime_title, mal_id=anime_id)
        else:
            anime = cast(Anime, cached) # type: ignore
        ## debug print...
        print(anime.openings)
        print(anime.title)
        print("")
        ## End of debug print


        #TODO: Add last updated check
        if len(anime.openings) == 0: #FIXME: This is not correct pls fix this if you see this, I did this from desperation, it was awfully slow and now is 11pm and I want to sleep, so don't judge me
            updateAnimeOpeningsList(Oauth, anime)
        db.session.add(anime)

        for op in anime.openings: # type: ignore
            json_out += [{
                "title": anime_title,
                "anime_id": anime.id,
                "mal_anime_id": anime_id,
                "op_title": op.opening_title,
                "op_artist": op.opening_artist,
                "op_uri": op.GetBestSong().spotify_link if op.GetBestSong() is not None else None,
            }] # type: ignore

    db.session.commit()
    # { 
    #     "title": cached.anime_title,
    #     "op_title": op.opening_title,
    #     "op_artist": op.artist.name,
    #     "op_uri": op.spotify_uri
    #  }
    return json.dumps(json_out)

AnimeData = dict[str, str|int]
def getAnimeList(auth: OAuth2) -> list[AnimeData]:
    """Gets the users anime list from MAL api"""
    URL: str = "https://api.myanimelist.net/v2/users/@me/animelist"
    anime_list: list[AnimeData] = []

    params: dict[str, str|int] = {
        'fields': 'list_status',
        "limit": 25,
        "offset": 0
    }
    while True:
        ret = rq.get(URL, params, auth=auth, timeout=150).json()

        if ret.get("error", None) is not None:
            raise Exception("animelist", ret["error"])

        for row in ret["data"]:
            anime_list.append({
                "id": row["node"]["id"],
                "title": row["node"]["title"],
                "status_data": row["list_status"],
            })

        if ret["paging"].get("next", None) is None:
            break
        params["offset"] += 25 # type: ignore / We know offset is always number
    return anime_list

def updateAnimeOpeningsList(auth: OAuth2, anime: Anime) -> list[Any]:
    """
    Gets the openings for the anime from MAL api and creates them in the DB

    auth
        OAuth2 object for MAL
    
    anime
        Anime object to get openings for (needs id set)
    """
    anime_id = int(anime.mal_id)
    assert anime_id is not None and type(anime_id) is int, f"Invalid Anime id, {anime_id=} | {type(anime_id)}"

    URL: str = f"https://api.myanimelist.net/v2/anime/{anime_id}"
    params = {
        "fields": "opening_themes"
    }
    ret = rq.get(URL, params=params, auth=auth, timeout=500).json()
    if ret.get("error", None) is not None:
        raise Exception("getAnimeOpeningList: ", ret["error"])


    openings: list[tuple[str,str,str]] = [parseOpStr(op_theme["text"]) for op_theme in ret.get("opening_themes", [])]
    for title, artist, _ in openings:
        db_opening = Opening.query.filter_by(opening_title=title, opening_artist=artist).one_or_none()

        if db_opening is None:
            op = Opening(opening_title=title, opening_artist=artist)
            anime.openings.append(op)
            db.session.add(op)
            db_opening = op

        # FIXME: Replace with magic function which asks spotify if none | gets from songs and returns uri
        #find if any song exists
        if db_opening.GetBestSong() is None:
            create_spotify_song(db_opening)


    # Ziskam openingy pro to anime
    return []


def parseOpStr(op_str: str) -> tuple[str, str, str]:
    """
    Parse the opening string into a tuple of (title, artist, episodes)

    op_str 
        The string to parse

    --------------------------------------------
    returns
        A tuple of (title, artist, episodes)
    """
    title: str
    artist: str
    episodes: str

    try:
        # Black magicry regex for parsing the opening string
        mtch = re.search(r'"([^()\n\r\"]+)(?: \(.+\))?\\?".*by ([\w\sö＆$%ěščřžýáíé\s]+)(?: \(.+\))?(?:.*\(eps\s(\d+-\d+)\))?', op_str)
        if mtch == None:
            raise Exception("regex", f"regex failed to match string {op_str}")
        title, artist, episodes = mtch.groups()
    except Exception as e:
        raise Exception("regex", f"regex failed to match string {op_str}") from e
    return (title, artist, episodes)
