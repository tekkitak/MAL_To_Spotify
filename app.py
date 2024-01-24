from flask import Flask, render_template, url_for, session, render_template_string
from flask_session import Session  # type: ignore -- package stub issue...
from flask_security import Security, auth_required, SQLAlchemyUserDatastore, hash_password
from datetime import datetime
from os import getenv

from model.actions import register_commands
from model.helper_functions import refresh_auth
from model.database import db, DB_VER, User, Role
from model.version_control import verControl
from controller.error import error
from controller.api_root import api
from controller.api.spotify import spotify_playlists

# Flask setup
app = Flask(__name__)
register_commands(app)
# config
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SECRET_KEY'] = getenv('FLASK_SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = getenv('DATABASE_URL')
app.config['SECURITY_PASSWORD_SALT'] = getenv('SECURITY_PASSWORD_SALT')
app.config['SECURITY_BLUEPRINT_NAME'] = 'security'
app.config['SECURITY_STATIC_FOLDER'] = 'security'
# routing
app.register_blueprint(error)
app.register_blueprint(api)
# SQLAlchemy
db.init_app(app)
# Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
app.security = Security(app, user_datastore)
# Session
Session(app)


@app.before_first_request
def check_version() -> None:
    # Checks for all the versioning done with versionControl
    if not verControl.compare('db_ver', str(DB_VER)):
        MSG = "Database version mismatch. Do you want to update the database? (y/n)\n"
        if input(MSG) == 'y':
            # FIXME: Extract into function that will be used by db_init and db_drop
            db.drop_all()
            db.create_all()
            verControl.update('db_ver', str(DB_VER))
        else:
            print("Quitting...")
            exit()
        verControl.save()


@app.route('/')
def index():
    playlists = []
    if session.get('spotify_access_token', False) is not False:
        if session['token_expiration_time'] < datetime.now():
            refresh_auth()
        playlists = spotify_playlists()['items']
    return render_template('index.j2',
                           Spotify_OAuth_url=url_for('api.spotify.spotifyAuth'),
                           MAL_OAuth_url=url_for('api.mal.malAuth'),
                           playlists=playlists
                           )

@app.route('/cradmin')
def cradmin():
    if not app.security.datastore.find_user(email="test@me.com"):
        app.security.datastore.create_user(email="test@me.com",
                                           password=hash_password("password"),
                                           username="Admin",
                                           active=True)
        db.session.commit()
        return 'Success'
    return 'Already exists'

@app.route('/test')
@auth_required()
def test():
    return render_template_string('Hello {{ current_user.username }}')
