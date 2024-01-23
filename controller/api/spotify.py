'''spotify.py - Spotify API controller'''
import json
from datetime import datetime, timedelta
from urllib.parse import urlencode
from typing import cast, Any
from os import getenv
import requests as rq
from flask import Blueprint, redirect, url_for, request, session
from model.database import db, Opening, Song, Artist
from model.helper_functions import exec_request, encode_base64

spotify = Blueprint('spotify', __name__,
                template_folder='templates/api/spotify',
                url_prefix='/spotify')


@spotify.route('/auth')
def spotify_auth():
    '''Spotify OAuth2 authentication'''
    if request.args.get('code', None) is None:
        url: str = "https://accounts.spotify.com/authorize"
        querystring: dict[str, Any] = {
            "client_id":getenv('SPOT_ID', None),
            "response_type":"code",
            "redirect_uri":"http://localhost:5000/api/spotify/auth",
            "scope":"playlist-modify-private playlist-modify-public user-library-read user-library-modify"
            }
        redirect_url: str = url + '?' + urlencode(querystring)
        return redirect(redirect_url)

    code: str = cast(str, request.args.get('code'))
    out = spotify_get_OAuth(code)
    if out is None:
        return redirect(url_for('index'))
    session['spotify_access_token'] = out['access_token']
    session['spotify_token_type'] = out['token_type']
    session['token_expiration_time'] = datetime.now() + timedelta(seconds=out['expires_in'])
    session['spotify_refresh_token'] = out['refresh_token']
    return redirect(url_for('index'))


def spotify_get_OAuth(code: str) -> Any:  # pylint: disable=invalid-name
    '''Gets OAuth2 token from spotify api'''
    assert getenv('SPOT_ID') is not None and getenv('SPOT_SECRET') is not None, 'SPOT_ID or SPOT_SECRET not set'
    spot_id:str = cast(str, getenv('SPOT_ID'))
    spot_secret:str = cast(str, getenv('SPOT_SECRET'))
    url = "https://accounts.spotify.com/api/token"
    body = {
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': 'http://localhost:5000/api/spotify/auth',
        'client_id': spot_id,
        'client_secret': spot_secret,
    }
    headers = {
        'Authorization': 'Basic ' + encode_base64(spot_id + ':' + spot_secret),
        'Content-type': 'application/x-www-form-urlencoded'
    }
    req = cast(rq.Response, exec_request(url, headers=headers, data=body, method='POST', auth=False))
    return req.json()


@spotify.route('/createPlaylist/<string:name>')
def create_spotify_playlist(name: str='MyAnimeList openings'):
    '''Creates playlist on spotify'''
    print(f'Creating playlist: {name}')
    user_profile = get_spotify_user_profile()
    user_id: str = cast(str, user_profile['id'])
    url: str = f"https://api.spotify.com/v1/users/{user_id}/playlists"
    data: str = '''\
        {
        "name":"''' + name + '''",
        "description":"Openings from my MyAnimeList",
        "public":"false"
        }\
    '''
    token_type, access_token = session['spotify_token_type'], session['spotify_access_token']  # type: ignore - Handled below by assert
    assert token_type is not None and access_token is not None, 'Spotify token not set'
    headers = {
        "Content-Type":"application/json",
        "Authorization": f"{token_type} {access_token}"
        }
    response = cast(rq.Response, exec_request(url, headers=headers, data=data, method='POST'))
    print(response.text)  # FIXME: Pryc s tim printem, at to je logging!
    return response.json()['id']


def get_spotify_user_profile() -> dict[str, Any]:
    '''Returns user profile from spotify api'''
    url = "https://api.spotify.com/v1/me"
    token_type, access_token = session['spotify_token_type'], session['spotify_access_token']  # type: ignore - Handled below by assert
    assert token_type is not None and access_token is not None, 'Spotify token not set'
    headers = {
        "Content-Type":"application/json",
        "Authorization": f"{token_type} {access_token}"
    }
    response = cast(rq.Response, exec_request(url, headers=headers, method='GET'))
    if response.status_code != 200:
        raise Exception('Error getting user profile')
    return response.json()


@spotify.route('/addSongs/<string:playlist_id>/<string:uris>')
def playlist_add_songs(uris: str, playlist_id: str):  # TODO: Remake to POST
    '''Adds songs to playlist'''
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"

    token_type, access_token = session['spotify_token_type'], session['spotify_access_token']  # type: ignore - Handled below by assert
    assert token_type is not None and access_token is not None, 'Spotify token not set'
    headers = {
        "Content-Type":"application/json",
        "Authorization": f"{token_type} {access_token}"
    }
    print (uris)  # FIXME: Pryc s tim printem, at to je logging!
    data = {
        "uris": uris.split(','),
        "position": 0
    }

    response = cast(rq.Response, exec_request(url, headers=headers, data=json.dumps(data), method='POST'))
    if response.status_code != 201:
        raise Exception('Error adding songs to playlist')
    return redirect(url_for('index'))


@spotify.route('/getSongUri/<string:name>/<string:artist>')  # type: ignore
def get_spotify_song(name:str | None=None, artist:str | None=None) -> None | dict[str, str]:
    '''Returns dict of song atributes from spotify api'''
    url = "https://api.spotify.com/v1/search"
    querystring = {
        "q":f"track:{name} artist:{artist}",
        "type":"track",
        "limit":"1"
        }

    token_type, access_token = session['spotify_token_type'], session['spotify_access_token']  # type: ignore - Handled below by assert
    assert token_type is not None and access_token is not None, 'Spotify token not set'
    headers = {
        "Content-Type":"application/json",
        "Authorization": f"{token_type} {access_token}"
    }
    response = cast(rq.Response, exec_request(url, headers=headers, params=querystring, method='GET'))  # FIXME: REMOVE THIS FUCKING BULLSHIT

    if response.status_code != 200:
        print(response.status_code)
        raise Exception('Error getting song uri')
    if response.json()['tracks']['total'] == 0:
        return None
    response = response.json()
    ret = {
        "uri": response['tracks']['items'][0]['uri'],
        "artist": response['tracks']['items'][0]['artists'][0]['name'],
        "song_name": response['tracks']['items'][0]['name']
     }
    return ret


@spotify.route('/playlists')
def spotify_playlists():
    '''Returns list of user's playlists'''
    url = "https://api.spotify.com/v1/me/playlists"

    token_type, access_token = session['spotify_token_type'], session['spotify_access_token']  # type: ignore - Handled below by assert
    assert token_type is not None and access_token is not None, 'Spotify token not set'
    headers = {
        "Content-Type":"application/json",
        "Authorization": f"{token_type} {access_token}"
    }
    response = cast(rq.Response, exec_request(url, headers=headers, method='GET'))

    if response.status_code != 200:
        raise Exception('Error getting user playlists')
    return response.json()


def create_spotify_song(op: Opening) -> bool:
    '''Creates song by searchin spotify for opening's title and artist.\n
    Returns True if song was created, False otherwise'''
    res = get_spotify_song(op.opening_title, op.opening_artist)
    if res is None:
        return False
    res = cast(dict[str, str], res)

    artist = Artist.query.filter_by(artist_name=res['artist']).first()
    if artist is None:
        artist = Artist(artist_name=res['artist'])
        db.session.add(artist)

    song = Song(
        song_title=res['song_name'],
        spotify_link=res['uri'],
        artist=artist,
    )

    db.session.add(song)
    op.songs.append(song)
    db.session.commit()
    return True


@spotify.route('/getSongInfo/<string:spotify_uri>')
def get_song_info(spotify_uri: str):
    '''Returns song info from spotify api'''
    url = f"https://api.spotify.com/v1/tracks/{spotify_uri.split(':')[2]}"

    token_type, access_token = session['spotify_token_type'], session['spotify_access_token']
    assert token_type is not None and access_token is not None, 'Spotify token not set'

    headers = {
        "Content-Type":"application/json",
        "Authorization": f"{token_type} {access_token}"
    }

    response = cast(rq.Response, exec_request(url, headers=headers, method='GET'))
    if response.status_code != 200:
        raise Exception('Error getting song info')
    return response.json()
