from flask import Blueprint, request
from model.database import db, Song, Opening, Artist
import json
from controller.api.spotify import get_song_info
from urllib.parse import unquote


suggestions = Blueprint('suggestions', __name__, 
                        template_folder='templates/api/suggestions', 
                        url_prefix='/suggestions')


@suggestions.route('/getSuggestions/<int:opening_id>')
def GetSuggestions(opening_id: int):
    opening = Opening.query.filter_by(id=opening_id).first()
    if opening == None:
        return 'Opening not found', 404
    print(opening)
    out: list[dict[str, str | int]] = []  # Explicitly define the types of dictionary keys and values
    for song in opening.songs:
        out.append({
            'song_title': song.song_title,
            'artist': song.artist.artist_name,
            'spotify_link': song.spotify_link,
            'votes': sum(vote.vote for vote in song.votes)
        })
    return json.dumps(out), 200

@suggestions.route('/addSuggestion', methods = ['POST'])
def AddSuggestion():
    data = request.get_json()
    print(data)
    if 'spotify_uri' not in data or 'opening_id' not in data:
        return 'No spotify uri or opening id provided', 400
    spotify_uri:str = data['spotify_uri']
    opening_id:int = int(data['opening_id'])
    opening = Opening.query.filter_by(id=opening_id).first()


    #if spotify uri is link, extract uri
    if spotify_uri.startswith('https:'):
        spotify_uri = "spotify:track:" + extractSpotifyUri(unquote(spotify_uri))
    
    #check if opening exists
    if opening == None:
        return 'Opening not found', 404
    song = Song.query.filter_by(spotify_link=spotify_uri).first()
    if song != None:
        return 'Song already exists', 409
    #search spotify for song info
    res = get_song_info(spotify_uri)

    if res is None:
        return 'Song not found', 404
    
    #check if artist exists
    artist = Artist.query.filter_by(artist_name=res['album']['artists'][0]['name']).first()
    if artist == None:
        #create artist
        artist = Artist(artist_name=res['album']['artists'][0]['name'])
        db.session.add(artist)
    
    #create song
    print(f"Creating song {res['name']} by {res['album']['artists'][0]['name']}")
    song = Song(
        song_title = res['name'],
        spotify_link = spotify_uri,
        artist = artist,
    )

    db.session.add(song)
    opening.songs.append(song)
    db.session.commit()
    return 'Song added', 200


def extractSpotifyUri(spotify_link: str) -> str:
    return spotify_link.split('/')[-1].split('?')[0]
