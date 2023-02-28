from datetime import datetime
import requests as rq
from flask import session, redirect, url_for
from os import getenv
from urllib.parse import urlencode
from datetime import datetime, timedelta
from base64 import b64encode as b64en


def exec_request(url, headers=None, params=None, data=None, method='GET', auth=True):

    if auth:
        if session.get('spotify_access_token', False) == False:
            # print('redirected for no token')
            return redirect(url_for('index'))
        if session.get('token_expiration_time') < datetime.now():
            # print('redirected for token expiration')
            refresh_auth()

    res = rq.request(method, url, headers=headers, params=params, data=data)
    
    print(f"exec: {res.status_code}")
    if res.status_code == 401:
        print('401 error')
        print(res.text)
        Exception(res.json()["error"])
    return res

def refresh_auth():
    print (session.get('spotify_access_token', False))
    url = "https://accounts.spotify.com/api/token"
    body = {
        'grant_type': 'refresh_token',
        'refresh_token': session.get('spotify_access_token', False),
    }
    headers = {
        'Authorization': 'Basic ' + encode_base64(getenv('SPOT_ID') + ':' + getenv('SPOT_SECRET')),
    }
    req = exec_request(url, headers=headers, data=body, method='POST', auth=False)
    print('refresh_auth')
    print(req.text)
    session['spotify_access_token'] = req.json()['access_token']
    session['token_expiration_time'] = datetime.now() + timedelta(seconds=req.json()['expires_in'])

def encode_base64(string):
    return b64en(string.encode('ascii')).decode('ascii')