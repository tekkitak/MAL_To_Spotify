from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Artist(db.Model):
    __tablename__ = 'artist'

    id = db.Column(db.Integer, primary_key=True)
    artist_name = db.Column(db.String(128), nullable=False)

    songs = db.relationship('Song', back_populates='artist', cascade='all, delete-orphan')

    def __repr__(self) -> str:
        return f'<Artist {self.id}, {self.artist_name}>'

class Anime(db.Model):
    __tablename__ = 'anime'

    id = db.Column(db.Integer, primary_key=True)
    mal_id = db.Column(db.Integer, nullable=True)
    title = db.Column(db.String(128), nullable=False)

    openings = db.relationship('Opening', secondary='anime_opening', back_populates='animes')

    def __repr__(self) -> str:
        return f'<Anime {self.id}, {self.anime_title}>'

class Opening(db.Model):
    __tablename__ = 'opening'

    id = db.Column(db.Integer, primary_key=True)
    opening_title = db.Column(db.String(128), nullable=False)

    songs = db.relationship('Song', back_populates='opening', cascade='all, delete-orphan')
    animes = db.relationship('Anime', secondary='anime_opening', back_populates='openings')

    def __repr__(self) -> str:
        return f'<Opening {self.id}, {self.opening_title}, {self.episodes}>'

class Song(db.Model):
    __tablename__ = 'song'

    id = db.Column(db.Integer, primary_key=True)
    song_title = db.Column(db.String(128), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'), nullable=False)
    artist = db.relationship('Artist', back_populates='songs')
    opening_id = db.Column(db.Integer, db.ForeignKey('opening.id'), nullable=False)
    opening = db.relationship('Opening', back_populates='songs')
    spotify_link = db.Column(db.String(128), nullable=False)

    votes = db.relationship('Vote', back_populates='song', cascade='all, delete-orphan')
    imports = db.relationship('Import', secondary='import_song', back_populates='songs')

    def __repr__(self) -> str:
        return f'<Song {self.id}, {self.song_title}, {self.artist}, {self.opening}, {self.spotify_link}>'

class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128), nullable=False)
    password = db.Column(db.String(128), nullable=False)
    myanimelist_id = db.Column(db.String(length=128), nullable=True)

    votes = db.relationship('Vote', back_populates='user', cascade='all, delete-orphan')
    oauth2s = db.relationship('OAuth2', back_populates='user', cascade='all, delete-orphan')
    syncs = db.relationship('Sync', back_populates='user', cascade='all, delete-orphan')
    imports = db.relationship('Import', back_populates='user', cascade='all, delete-orphan')

    def __repr__(self) -> str:
        return f'<User {self.id}, {self.username}, {self.password}, {self.myanimelist_id}>'

class Vote(db.Model):
    __tablename__ = 'vote'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', back_populates='votes')
    song_id = db.Column(db.Integer, db.ForeignKey('song.id'), nullable=False)
    song = db.relationship('Song', back_populates='votes')
    vote = db.Column(db.Integer, nullable=False)

class Import(db.Model):
    __tablename__ = 'import'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', back_populates='imports')
    time= db.Column(db.DateTime, nullable=False)
    songs = db.relationship('Song', secondary='import_song', back_populates='imports')

class OAuth2(db.Model):
    __tablename__ = 'oauth2'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', back_populates='oauth2s')
    provider = db.Column(db.String(128), nullable=False)
    access_token = db.Column(db.String(128), nullable=False)
    token_type = db.Column(db.String(128), nullable=False)
    refresh_token = db.Column(db.String(128), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)

class Sync(db.Model):
    __tablename__ = 'sync'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', back_populates='syncs')
    provider = db.Column(db.String(128), nullable=False)
    last_synced_at = db.Column(db.DateTime, nullable=False)

anime_opening = db.Table(
    'anime_opening',
    db.Column('anime_id', db.Integer, db.ForeignKey('anime.id'), primary_key=True),
    db.Column('opening_id', db.Integer, db.ForeignKey('opening.id'), primary_key=True),
    db.Column('episodes', db.String(128), nullable=False)
)

import_song = db.Table(
    'import_song',
    db.Column('import_id', db.Integer, db.ForeignKey('import.id'), primary_key=True),
    db.Column('song_id', db.Integer, db.ForeignKey('song.id'), primary_key=True)
)