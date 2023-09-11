from typing import List
from sqlalchemy import Column, DateTime, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Base(DeclarativeBase):
    pass 

class Artist(Base):
    __tablename__ = 'artist'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)

    songs: Mapped[List['Song']] = relationship(back_populates='artist')

    def __repr__(self) -> str:
        return f'<Artist {self.id}, {self.name}>'
    

anime_opening = Table(
    "anime_opening",
    Base.metadata,
    Column("anime_id", Integer, ForeignKey("anime.id")),
    Column("opening_id", Integer, ForeignKey("opening.id")),
    Column("episodes", String(128), nullable=False),
)    

class Opening(Base):
    __tablename__ = 'opening'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    opening_title: Mapped[str] = mapped_column(String(128), nullable=False)
    episodes: Mapped[str] = mapped_column(String(128), nullable=False)

    songs: Mapped[List['Song']] = relationship(back_populates='opening')
    animes: Mapped[List['Anime']] = relationship('Anime', secondary=anime_opening, back_populates='openings')

    def __repr__(self) -> str:
        return f'<Opening {self.id}, {self.opening_title}, {self.episodes}>'
    
class Anime(Base):
    __tablename__ = 'anime'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    anime_title: Mapped[str] = mapped_column(String(128), nullable=False)

    openings: Mapped[List['Opening']] = relationship('Opening', secondary=anime_opening, back_populates='animes')

    def __repr__(self) -> str:
        return f'<Anime {self.id}, {self.anime_title}>'
    
import_song = Table(
    "import_song",
    Base.metadata,
    Column("import_id", Integer, ForeignKey("import.id")),
    Column("song_id", Integer, ForeignKey("song.id")),
)

class Import(Base):
    __tablename__ = 'import'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('user.id'), nullable=False)
    user: Mapped['User'] = relationship(back_populates='import')
    time: Mapped[DateTime] = mapped_column(DateTime, nullable=False)

    songs: Mapped[List['Song']] = relationship('Song', secondary=import_song, back_populates='imports')

    def __repr__(self) -> str:
        return f'<Import {self.id}, {self.user}, {self.time}>'

class Song(Base):
    __tablename__ = 'song'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    song_title: Mapped[str] = mapped_column(String(128), nullable=False)
    artist_id: Mapped[int] = mapped_column(Integer, ForeignKey('artist.id'), nullable=False)
    artist: Mapped['Artist'] = relationship(back_populates='songs')
    opening_id: Mapped[int] = mapped_column(Integer, ForeignKey('opening.id'), nullable=False)
    opening: Mapped['Opening'] = relationship(back_populates='songs')
    spotify_link: Mapped[str] = mapped_column(String(128), nullable=False)

    votes: Mapped[List['Vote']] = relationship(back_populates='song')
    imports: Mapped[List['Import']] = relationship('Import', secondary=import_song, back_populates='songs')

    def __repr__(self) -> str:
        return f'<Song {self.id}, {self.song_title}, {self.artist}, {self.opening}, {self.spotify_link}>'

class User(Base):
    __tablename__ = 'user'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(128), nullable=False)
    password: Mapped[str] = mapped_column(String(128), nullable=False)
    myanimelist_id: Mapped[int] = mapped_column(String(length=128), nullable=False)

    votes: Mapped[List['Vote']] = relationship(back_populates='user')
    oauth2s: Mapped[List['OAuth2']] = relationship(back_populates='user')
    syncs: Mapped[List['Sync']] = relationship(back_populates='user')
    imports: Mapped[List['Import']] = relationship(back_populates='user')

    def __repr__(self) -> str:
        return f'<User {self.id}, {self.username}, {self.password}, {self.myanimelist_id}>'
    
class Vote(Base):
    __tablename__ = 'vote'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('user.id'), nullable=False)
    user: Mapped['User'] = relationship(back_populates='votes')
    song_id: Mapped[int] = mapped_column(Integer, ForeignKey('song.id'), nullable=False)
    song: Mapped['Song'] = relationship(back_populates='votes')
    vote: Mapped[int] = mapped_column(Integer, nullable=False)

    def __repr__(self) -> str:
        return f'<Vote {self.id}, {self.user}, {self.song}, {self.vote}>'

class OAuth2(Base):
    __tablename__ = 'oauth2'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('user.id'), nullable=False)
    user: Mapped['User'] = relationship(back_populates='oauth2')
    access_token: Mapped[str] = mapped_column(String(128), nullable=False)
    token_type: Mapped[str] = mapped_column(String(128), nullable=False)
    refresh_token: Mapped[str] = mapped_column(String(128), nullable=False)
    expires_at: Mapped[int] = mapped_column(Integer, nullable=False)

    def __repr__(self) -> str:
        return f'<OAuth2 {self.id}, {self.user}, {self.access_token}, {self.token_type}, {self.refresh_token}, {self.expires_at}>'


class Sync(Base):
    __tablename__ = 'sync'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('user.id'), nullable=False)
    user: Mapped['User'] = relationship(back_populates='sync')
    last_sync: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    spotify_playlist_id: Mapped[str] = mapped_column(String(128), nullable=False)
    spotify_oauth2_id: Mapped[int] = mapped_column(Integer, ForeignKey('oauth2.id'), nullable=False)
    spotify_oauth2: Mapped['OAuth2'] = relationship(back_populates='sync')
    myanimelist_oauth2_id: Mapped[int] = mapped_column(Integer, ForeignKey('oauth2.id'), nullable=False)
    myanimelist_oauth2: Mapped['OAuth2'] = relationship(back_populates='sync')

    def __repr__(self) -> str:
        return f'<Sync {self.id}, {self.user}, {self.last_sync}, {self.spotify_playlist_id}, {self.spotify_oauth2}, {self.myanimelist_oauth2}>'
        