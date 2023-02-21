import secrets
from os import getenv
from flask import session
from urllib.parse import urlencode
import requests as rq
from time import time

def get_new_code() -> str:
    token = secrets.token_urlsafe(100)
    return token[:128]

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
        raise Exception(req.json()["error"])
    return req.json()

def mal_auth_user_url():
    if session.get('mal_verifier', None) == None or time() > session.get('mal_verifier_expire', 1):
        session['mal_verifier'] = get_new_code()
        session['mal_verifier_expire'] = time() + 600
    
    url = "https://myanimelist.net/v1/oauth2/authorize"
    params = {
        'response_type': 'code', 
        'client_id': getenv('MAL_ID'), 
        'redirect_uri': 'http://localhost:5000/auth/mal', 
        'code_challenge_method': 'plain',
        'code_challenge': session['mal_verifier']
    }

    return url + '?' + urlencode(params)

def mal_is_valid() -> bool:
    if session.get('mal_access_token', None) == None:
        return False
    if session.get('mal_refresh_token', None) == None:
        return False
    if session.get('mal_access_token_expire', 1) < time():
        return False
    return True

def mal_refresh_token():
    pass