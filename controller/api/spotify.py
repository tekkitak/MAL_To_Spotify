'''Module for Spotify API'''
from os import getenv
from typing import Any, Optional, cast
import requests as rq
from flask import Blueprint, redirect, request, session, url_for
from model.oauth2 import OAuth2, SpotifyOAuth2Builder
from model.database import Opening, Artist, Song, db

spotify = Blueprint(
    name = "spotify",
    import_name = __name__,
    template_folder = "templates/api/spotify",
    url_prefix = "/spotify"
)

@spotify.route("/auth")
def spotifyAuth():
    '''Authenticate Spotify API'''
    if session.get("spotify_oauth", None) is None:
        session["spotify_oauth"] = SpotifyOAuth2Builder(
            client_id = getenv("SPOT_ID"),
            client_secret = getenv("SPOT_SECRET"),
            redirect_url = "http://localhost:5000/api/spotify/auth"
        )
        return redirect(session["spotify_oauth"].get_auth_url())

    if request.args.get("code", None) is None:
        return redirect(session["spotify_oauth"].get_auth_url())

    session["spotify_oauth"].token_from_code(request.args.get("code"))
    return redirect(url_for("index"))

@spotify.route("/createPlaylist/<string:name>")
def createPlaylist(name: str):
    '''Create a playlist'''
    Oauth: Optional[OAuth2] = cast(Optional[OAuth2], session.get("spotify_oauth", None))
    if Oauth is None:
        return redirect("spotifyAuth")

    user_id: str = cast(str, get_spotify_user_profile()["id"])
    url:str = f"https://api.spotify.com/v1/users/{user_id}/playlists"
    headers: dict[str, str] = {
        "Authorization": Oauth.get_Bearer(),
        "Content-Type": "application/json"
    }
    data: dict[str, str | bool] = {
        "name": name,
        "public": False
    }
    req = rq.post(url=url, headers=headers, json=data, auth=Oauth, timeout=150)
    return req.json()

def get_spotify_user_profile() -> dict[str, Any]:
    '''Get user profile'''
    Oauth: Optional[OAuth2] = cast(Optional[OAuth2], session.get("spotify_oauth", None))
    if Oauth is None:
        return redirect("spotifyAuth")

    url:str = "https://api.spotify.com/v1/me"
    headers: dict[str, str] = {
        "Authorization": Oauth.get_Bearer(),
        "Content-Type": "application/json"
    }
    req = rq.get(url=url, headers=headers, auth=Oauth, timeout=150)
    return req.json()

@spotify.route("/addSong/<string:playlist_id>/<string:uris>")
def playlist_add_song(playlist_id: str, uris: str):
    '''Add a song to a playlist'''
    Oauth: Optional[OAuth2] = cast(Optional[OAuth2], session.get("spotify_oauth", None))
    if Oauth is None:
        return redirect("spotifyAuth")

    url:str = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    headers: dict[str, str] = {
        "Authorization": Oauth.get_Bearer(),
        "Content-Type": "application/json"
    }
    data = {
        "uris": uris.split(",")
    }
    req = rq.post(url=url, headers=headers, json=data, auth=Oauth, timeout=150)
    return req.json()

def get_spotify_song(name: str, artist: str):
    '''Get a song URI'''
    Oauth: Optional[OAuth2] = cast(Optional[OAuth2], session.get("spotify_oauth", None))
    if Oauth is None:
        return redirect("spotifyAuth")

    url:str = "https://api.spotify.com/v1/search"
    headers: dict[str, str] = {
        "Authorization": Oauth.get_Bearer(),
        "Content-Type": "application/json"
    }
    params: dict[str, str] = {
        "q": f"track:{name} artist:{artist}",
        "type": "track"
    }
    res = rq.get(url=url, headers=headers, params=params, auth=Oauth, timeout=150)
    res = res.json()
    if res["tracks"]["total"] == 0:
        return None
    return {
        "uri": res["tracks"]["items"][0]["uri"],
        "artist": res["tracks"]["items"][0]["artists"][0]["name"],
        "song_name": res["tracks"]["items"][0]["name"]
    }

@spotify.route("/playlists")
def spotify_playlists():
    '''Get user playlists'''
    Oauth: Optional[OAuth2] = cast(Optional[OAuth2], session.get("spotify_oauth", None))
    if Oauth is None:
        return redirect("spotifyAuth")

    url:str = "https://api.spotify.com/v1/me/playlists"
    headers: dict[str, str] = {
        "Authorization": Oauth.get_Bearer(),
        "Content-Type": "application/json"
    }
    res = rq.get(url=url, headers=headers, auth=Oauth, timeout=150)
    return res.json()

def create_spotify_song(op: Opening) -> bool:
    '''Creates song by searchin spotify for opening's title and artist.\n
    Returns True if song was created, False otherwise'''
    res = get_spotify_song(op.opening_title, op.opening_artist)
    if res is None:
        return False
    res = cast(dict[str, str], res)

    artist = Artist.query.filter_by(artist_name=res["artist"]).first()
    if artist is None:
        artist = Artist(artist_name=res["artist"])
        db.session.add(artist)

    song = Song(
        song_title=res["song_name"],
        spotify_link=res["uri"],
        artist=artist,
    )

    db.session.add(song)
    op.songs.append(song)
    db.session.commit()
    return True

@spotify.route("/getSongInfo/<string:spotify_uri>")
def get_song_info(spotify_uri: str):
    '''Get song info'''
    url = f"https://api.spotify.com/v1/tracks/{spotify_uri.split(':')[2]}"

    headers = {
        "Authorization": session["spotify_oauth"].get_Bearer(),
        "Content-Type": "application/json"
    }
    response = cast(rq.Response, rq.get(url, headers=headers))

    return response.json()
