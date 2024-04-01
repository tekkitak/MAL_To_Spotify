'''database.py - Database ORM'''

# type: ignore
from typing import List, Optional, cast
from flask_sqlalchemy import SQLAlchemy
from flask_security.models import fsqla_v2 as fsqla
import requests as rq

db = SQLAlchemy()
DB_VER = 1.5
fsqla.FsModels.set_db_info(db)


class Artist(db.Model):
    '''ORM for artist table'''
    __tablename__ = "artist"

    id = db.Column(db.Integer, primary_key=True)
    artist_name = db.Column(db.String(128), nullable=False)

    songs = db.relationship(
        "Song", back_populates="artist", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Artist {self.id}, {self.artist_name}>"




class Anime(db.Model):
    '''ORM for anime table'''
    __tablename__ = "anime"

    id = db.Column(db.Integer, primary_key=True)
    mal_id = db.Column(db.Integer, nullable=True)
    title = db.Column(db.String(128), nullable=False)
    last_updated = db.Column(db.DateTime, nullable=True)

    openings = db.relationship(
        "Opening", secondary="anime_opening", back_populates="animes"
    )
    anime_openings = db.relationship("Anime_opening", back_populates="anime", overlaps="animes,openings")

    def __repr__(self) -> str:
        return f"<Anime {self.id}, {self.anime_title}>"




class Opening(db.Model):
    '''ORM for opening table'''
    __tablename__ = "opening"

    id = db.Column(db.Integer, primary_key=True)
    opening_title = db.Column(db.String(128), nullable=False)
    opening_artist = db.Column(db.String(128), nullable=False)
    last_updated = db.Column(db.DateTime, nullable=True)

    songs = db.relationship(
        "Song", back_populates="opening", cascade="all, delete-orphan"
    )

    animes = db.relationship(
        "Anime", secondary="anime_opening", back_populates="openings"
    )
    anime_openings = db.relationship("Anime_opening", back_populates="opening", overlaps="openings,animes")

    def __repr__(self) -> str:
        return f"<Opening {self.id}, {self.opening_title}>"

    def GetBestSong(self) -> "Song | None":
        '''Returns song with most votes'''
        if len(self.songs) == 0:
            return None
        return max(self.songs, key=lambda song: sum(vote.vote for vote in song.votes))


class Song(db.Model):
    '''ORM for song table'''
    __tablename__ = "song"

    id = db.Column(db.Integer, primary_key=True)
    song_title = db.Column(db.String(128), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey("artist.id"), nullable=False)
    artist = db.relationship("Artist", back_populates="songs")
    opening_id = db.Column(db.Integer, db.ForeignKey("opening.id"), nullable=True)
    opening = db.relationship("Opening", back_populates="songs")
    spotify_link = db.Column(db.String(128), nullable=False)

    votes = db.relationship("Vote", back_populates="song", cascade="all, delete-orphan")
    # imports = db.relationship("Import", secondary="import_song", back_populates="songs")
    imports = db.relationship("Import", secondary="import_song", back_populates="songs")

    def __repr__(self) -> str:
        return f"<Song {self.id}, {self.song_title}, {self.artist}, {self.opening}, {self.spotify_link}>"



class User(db.Model, fsqla.FsUserMixin):
    '''ORM for user table'''
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    # username = db.Column(db.String(128), nullable=False)
    password = db.Column(db.String(128), nullable=False)
    myanimelist_id = db.Column(db.String(length=128), nullable=True)

    votes = db.relationship("Vote", back_populates="user", cascade="all, delete-orphan")
    oauth2s = db.relationship(
        "OAuth2", back_populates="user", cascade="all, delete-orphan"
    )
    syncs = db.relationship("Sync", back_populates="user", cascade="all, delete-orphan")
    imports = db.relationship(
        "Import", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<User {self.id}, {self.username}, {self.password}, {self.myanimelist_id}>"
        )

    def has_role(self, role) -> bool:
        return role in self.roles

    def print_roles(self) -> str:
        return ', '.join(role.name for role in self.roles)


class Role(db.Model, fsqla.FsRoleMixin):
    __tablename__ = "role"



class Vote(db.Model):
    '''ORM for vote table'''
    __tablename__ = "vote"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User", back_populates="votes")
    song_id = db.Column(db.Integer, db.ForeignKey("song.id"), nullable=False)
    song = db.relationship("Song", back_populates="votes")
    vote = db.Column(db.Integer, nullable=False)


class Import(db.Model):
    '''ORM for import table'''
    __tablename__ = "import"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User", back_populates="imports")
    time = db.Column(db.DateTime, nullable=False)
    # songs = db.relationship("Song", secondary="import_song", back_populates="imports")
    songs = db.relationship("Song", secondary="import_song", back_populates="imports")
    import_songs = db.relationship("Import_song", back_populates="from_import", overlaps="imports,songs")



class OAuth2(db.Model):
    '''ORM for oauth2 table'''
    __tablename__ = "oauth2"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User", back_populates="oauth2s")
    provider = db.Column(db.String(128), nullable=False)
    provider_user_id = db.Column(db.Integer, nullable=True)
    token_type = db.Column(db.String(128), nullable=False)
    allow_login = db.Column(db.Boolean, nullable=False)



class Sync(db.Model):
    '''ORM for sync table'''
    __tablename__ = "sync"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User", back_populates="syncs")
    provider = db.Column(db.String(128), nullable=False)
    last_synced_at = db.Column(db.DateTime, nullable=False)


class Anime_opening(db.Model):
    __tablename__ = "anime_opening"

    anime_id = db.Column(db.Integer, db.ForeignKey("anime.id"), primary_key=True)
    anime = db.relationship("Anime", back_populates="anime_openings", overlaps="animes,openings")
    opening_id = db.Column(db.Integer, db.ForeignKey("opening.id"), primary_key=True)
    opening = db.relationship("Opening", back_populates="anime_openings", overlaps="openings,animes")
    episodes = db.Column(db.String(128), nullable=True)


class Import_song(db.Model):
    __tablename__ = "import_song"

    import_id = db.Column(db.Integer, db.ForeignKey("import.id"), primary_key=True)
    from_import = db.relationship("Import", back_populates="import_songs", overlaps="imports,songs")
    song_id = db.Column(db.Integer, db.ForeignKey("song.id"), primary_key=True)

    @classmethod
    def stats_by_songs(cls, limit, offset) -> list[dict[str, str | int]]:
        """Get the count of imports by song"""
        ret = db.session.query(
                    cls.song_id, Song.song_title, Artist.artist_name,
                    db.func.count(cls.song_id).label("count")
                ).select_from(cls).join(Song).join(Artist).group_by(
                    cls.song_id, Song.song_title, Artist.artist_name
                ).order_by(db.desc("count")).limit(limit).offset(offset).all()
        return [{"id": song_id, "song": song_title, "artist": artist_name, "count": count} for song_id, song_title, artist_name, count in ret]
