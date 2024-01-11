from flask import Blueprint
from model.database import db, Song, Anime, Vote, Opening, Artist
import json
from controller.api.spotify import get_song_info


suggestions = Blueprint('suggestions', __name__, 
                        template_folder='templates/api/suggestions', 
                        url_prefix='/suggestions')


@suggestions.route('/getSuggestions/<int:opening_id>')
def GetSuggestions(opening_id: int):
    opening = Opening.query.filter_by(id=opening_id).first()
    if opening == None:
        return 'Opening not found', 404
    return json.dumps(opening.songs, default=lambda x: x.__dict__)


@suggestions.route('/addSuggestion/<int:opening_id>/<string:spotify_uri>')
def AddSuggestion(opening_id: int, spotify_uri: str):
    opening = Opening.query.filter_by(id=opening_id).first()
    if opening == None:
        return 'Opening not found', 404
    song = Song.query.filter_by(spotify_link=spotify_uri).first()
    if song != None:
        return 'Song already exists', 409
    #search spotify for song info
    res = get_song_info(spotify_uri)

    if res is None:
        return 'Song not found', 404
    res = json.loads(res)
    
    #check if artist exists
    artist = Artist.query.filter_by(artist_name=res['artist']).first()
    if artist == None:
        #create artist
        artist = Artist(artist_name=res['artist'])
        db.session.add(artist)
    
    #if spotify uri is link, extract uri
    if spotify_uri.startswith('https://open.spotify.com/'):
        spotify_uri = extractSpotifyUri(spotify_uri)

    #create song
    song = Song(
        song_title = res['song_name'],
        spotify_link = spotify_uri,
        artist = artist,
    )

    db.session.add(song)
    opening.songs.append(song)
    db.session.commit()
    return 'Song added', 200


def extractSpotifyUri(spotify_link: str) -> str:
    return spotify_link.split('/')[-1].split('?')[0]
