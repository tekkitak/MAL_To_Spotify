from flask import Flask, render_template, redirect, url_for, request, session
from flask_session import Session
from urllib.parse import urlencode
import requests as rq
from os import getenv

from helper_functions import get_new_code


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



def mal_get_OAuth(code):
    url = "https://myanimelist.net/v1/oauth2/token"
    params = {
        'client_id': getenv('MAL_ID'),
        'client_secret': getenv('MAL_SECRET'),
        'code': code,
        'code_verifier': session['mal_verifier'],
        'grant_type': 'authorization_code',
        'redirect_uri': 'http://localhost:5000/auth/mal'
    }
    req = rq.post(url, data=params)
    if req.json().get('error', None) != None:
        raise Exception(req.json()['error'])
    return req.json()

def mal_auth_user_url():
    if session.get('mal_verifier', None) == None:
        session['mal_verifier'] = get_new_code()
    
    url = "https://myanimelist.net/v1/oauth2/authorize"
    params = {
        'response_type': 'code', 
        'client_id': getenv('MAL_ID'), 
        'redirect_uri': 'http://localhost:5000/auth/mal', 
        'code_challenge_method': 'plain',
        'code_challenge': session['mal_verifier']
    }

    return url + '?' + urlencode(params)