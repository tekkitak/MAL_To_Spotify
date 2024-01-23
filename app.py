'''Main file for the Flask app.'''
from datetime import datetime
from os import getenv
from flask import Flask, render_template, url_for, session
from flask_session import Session  # type: ignore -- package stub issue...
from model.actions import register_commands
from model.helper_functions import refresh_auth
from model.database import db, DB_VER
from model.version_control import VersionControl
from controller.error import error
from controller.api_root import api
from controller.api.spotify import spotify_playlists

app = Flask(__name__)
register_commands(app)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SECRET_KEY'] = getenv('FLASK_SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = getenv('DATABASE_URL')
app.register_blueprint(error)
app.register_blueprint(api)
db.init_app(app)
Session(app)


@app.before_first_request
def check_version() -> None:
    '''Checks if all versions match'''
    ver_control = VersionControl()
    # Checks for all the versioning done with versionControl
    if not ver_control.compare('db_ver', str(DB_VER)):
        msg = "Database version mismatch. Do you want to update the database? (y/n)\n"
        if input(msg) == 'y':
            # FIXME: Extract into function that will be used by db_init and db_drop
            db.drop_all()
            db.create_all()
            ver_control.update('db_ver', str(DB_VER))
        else:
            print("Quitting...")
            exit()
    ver_control.save()


@app.route('/')
def index():
    '''Index page'''
    playlists = []
    if session.get('spotify_access_token', False) is not False:
        if session['token_expiration_time'] < datetime.now():
            refresh_auth()
        playlists = spotify_playlists()['items']
    return render_template('index.j2',
                           Spotify_OAuth_url=url_for('api.spotify.spotify_auth'),
                           MAL_OAuth_url=url_for('api.mal.malAuth'),
                           playlists=playlists
                          )
