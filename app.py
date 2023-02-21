from flask import Flask, render_template, redirect, url_for, request, session
from flask_session import Session
from urllib.parse import urlencode
import requests as rq
from os import getenv
import json

from helper_functions import get_new_code, mal_get_OAuth, mal_auth_user_url, mal_is_valid, mal_refresh_token


app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SECRET_KEY'] = getenv('FLASK_SECRET_KEY')
Session(app)




@app.route('/')
def index():
    return render_template('index.html', MAL_OAuth_url=url_for('malAuth'))

@app.route('/auth/mal')
def malAuth(): 
    if request.args.get('code', None) == None:
        return redirect(mal_auth_user_url())
    
    code = request.args.get('code')
    out = mal_get_OAuth(code)
    session['mal_access_token'] = out['access_token']
    session['mal_refresh_token'] = out['refresh_token']
    

    return redirect(url_for('index'))

@app.route('/mal/animeOpList')
def malAnimeOpList():
    op_list =  []
    anime_list = []
    if not mal_is_valid():
        mal_refresh_token()
    auth_str = "Bearer " + session["mal_access_token"]
    
    url = "https://api.myanimelist.net/v2/users/@me/animelist"
    offset = 0
    while True:
        ret = rq.get(url, params={'fields': 'list_status', "limit": 25, "offset": offset}, headers={"Authorization": auth_str}).json()
        if ret.get("error", None) != None:
            raise Exception("animelist", ret["error"])
        anime_list += ret["data"]
        if ret["paging"].get("next", None) == None:
            break
        offset += 25
    if session.get("mal_anime_cache", None) == None:
        session["mal_anime_cache"] = []
    for anime in anime_list:
        if request.args.get("completed_only", "true") == "true" and anime["list_status"]["status"] != "completed":
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
        ret = rq.get(url, params={"fields": "opening_themes"}, headers={"Authorization": auth_str}).json()
        if ret.get("error", None) != None:
            raise Exception("animedetails", ret["error"])

        anime_data["op"] = [x["text"] for x in ret.get("opening_themes", [])]
        
        op_list.append(anime_data)
        session["mal_anime_cache"].append(anime_data)
    return json.dumps(op_list)