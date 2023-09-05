from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

anime_openings = db.Table("anime_openings",
    db.Column('anime_id', db.Integer, db.ForeignKey('anime.id'), primary_key=True),
    db.Column('opening_id', db.Integer, db.ForeignKey('opening.id'), primary_key=True)
                          )
                        
class Artist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    openings = db.relationship('Opening', backref='artist')
    __table_args__ = (db.UniqueConstraint('name', name='_artist_uc'),)
    def __repr__(self):
        return f"<Artist#{self.id} {self.name}>"

class Opening(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    opening_title = db.Column(db.String, nullable=False)
    episodes = db.Column(db.String(32), nullable=False)
    def __repr__(self):
        return f"<Opening#{self.id} {self.opening_title}>"

class Song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    song_title = db.Column(db.String(255), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'), nullable=False)
    opening = db.relationship('Opening', backref='song')
    spotify_url = db.Column(db.String(255), nullable=False)
    votes = db.Column(db.Integer, nullable=False, default=0)
    # __table_args__ = (db.UniqueConstraint('id', 'song_title', name='_song_uc'),)
    def __repr__(self):
        return f"<Song#{self.id} {self.song_title}>"

class Anime(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    anime_title = db.Column(db.String(255), nullable=False)
    openings = db.relationship('Opening', secondary=anime_openings, backref='anime')
    __table_args__ = (db.UniqueConstraint('id', 'anime_title', name='_anime_uc'),)
    def __repr__(self):
        return f"<Anime#{self.id} {self.anime_title}>"
