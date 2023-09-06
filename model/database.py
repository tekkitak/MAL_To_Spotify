from typing import List
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Base(DeclarativeBase):
    pass 



anime_openings = db.Table("anime_openings",
    Base.metadata,
    Column('anime_id', ForeignKey('anime.id'), primary_key=True),
    Column('opening_id', ForeignKey('opening.id'), primary_key=True)
)


class Artist(Base):
    __tablename__ = 'artist'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    openings = relationship('opening', backref='artist')
    __table_args__ = (db.UniqueConstraint('name', name='_artist_uc'),)
    def __repr__(self):
        return f"<Artist#{self.id} {self.name}>"

class Opening(Base):
    __tablename__ = 'opening'
    id = Column(Integer, primary_key=True)
    opening_title = Column(String, nullable=False)
    episodes = Column(String(32), nullable=False)
    def __repr__(self):
        return f"<Opening#{self.id} {self.opening_title}>"

class Song(Base):
    __tablename__ = 'song'
    id = Column(Integer, primary_key=True)
    song_title = Column(String(255), nullable=False)
    artist_id = Column(Integer, ForeignKey('artist.id'), nullable=False)
    opening_id = Column(Integer, ForeignKey('opening.id'), nullable=False)
    spotify_url = Column(String(255), nullable=False)
    votes = Column(Integer, nullable=False, default=0)
    # __table_args__ = (db.UniqueConstraint('id', 'song_title', name='_song_uc'),)
    def __repr__(self):
        return f"<Song#{self.id} {self.song_title}>"


class Anime(Base):
    __tablename__ = 'anime'
    id = Column(Integer, primary_key=True)
    anime_title = Column(String(255), nullable=False)
    openings: Mapped[List[Opening]]= relationship(secondary=anime_openings)
    __table_args__ = (db.UniqueConstraint('id', 'anime_title', name='_anime_uc'),)
    def __repr__(self):
        return f"<Anime#{self.id} {self.anime_title}>"
