from flask import Flask, render_template, redirect, url_for, request, session
from flask_session import Session
from urllib.parse import urlencode
import requests as rq
from os import getenv
import json
from oauth2 import OAuth2, MalOAuth2Builder

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SECRET_KEY'] = getenv('FLASK_SECRET_KEY')
Session(app)




@app.route('/')
def index():
    return render_template('index.j2', MAL_OAuth_url=url_for('malAuth'))

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