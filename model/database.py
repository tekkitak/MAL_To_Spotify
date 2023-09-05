from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Base(declarative_base()):
    pass


anime_openings = db.Table("anime_openings",
    Column('anime_id', Integer, ForeignKey('anime.id'), primary_key=True),
    Column('opening_id', Integer, ForeignKey('opening.id'), primary_key=True)
                          )
                        
class Artist(Base):
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    openings = relationship('Opening', backref='artist')
    __table_args__ = (db.UniqueConstraint('name', name='_artist_uc'),)
    def __repr__(self):
        return f"<Artist#{self.id} {self.name}>"

class Opening(Base):
    id = Column(Integer, primary_key=True)
    opening_title = Column(String, nullable=False)
    episodes = Column(String(32), nullable=False)
    def __repr__(self):
        return f"<Opening#{self.id} {self.opening_title}>"

class Song(Base):
    id = Column(Integer, primary_key=True)
    song_title = Column(String(255), nullable=False)
    artist_id = Column(Integer, ForeignKey('artist.id'), nullable=False)
    opening = relationship('Opening', backref='song')
    spotify_url = Column(String(255), nullable=False)
    votes = Column(Integer, nullable=False, default=0)
    # __table_args__ = (db.UniqueConstraint('id', 'song_title', name='_song_uc'),)
    def __repr__(self):
        return f"<Song#{self.id} {self.song_title}>"

class Anime(Base):
    id = Column(Integer, primary_key=True)
    anime_title = Column(String(255), nullable=False)
    openings = relationship('Opening', secondary=anime_openings, backref='anime')
    __table_args__ = (db.UniqueConstraint('id', 'anime_title', name='_anime_uc'),)
    def __repr__(self):
        return f"<Anime#{self.id} {self.anime_title}>"