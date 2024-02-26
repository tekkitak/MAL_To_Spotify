from flask import Flask, render_template, url_for, session, render_template_string
from flask_session import Session  # type: ignore -- package stub issue...
from flask_security import Security, auth_required, SQLAlchemyUserDatastore, hash_password, user_registered
from datetime import datetime
from os import getenv

from model.actions import register_commands
from model.helper_functions import refresh_auth
from model.database import db, DB_VER, User, Role
from model.version_control import verControl
from controller.error import error
from controller.api_root import api
from controller.user import user
from controller.api.spotify import spotify_playlists

# Flask setup
app = Flask(__name__)
register_commands(app)


# config
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SECRET_KEY'] = getenv('FLASK_SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = getenv('DATABASE_URL')
# Flask-Security config
app.config['SECURITY_PASSWORD_SALT'] = getenv('SECURITY_PASSWORD_SALT')
app.config['SECURITY_BLUEPRINT_NAME'] = 'security'
app.config['SECURITY_STATIC_FOLDER'] = 'security'
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_SEND_REGISTER_EMAIL'] = False
app.config['SECURITY_EMAIL_SENDER'] = None
app.config['SECURITY_USERNAME_ENABLE'] = True
app.config['SECURITY_USERNAME_REQUIRED'] = True
app.config["SECURITY_CONFIRMABLE"] = False
app.config["SECURITY_WAN_ALLOW_AS_FIRST_FACTOR"] = True
# routing
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# have session and remember cookie be samesite (flask/flask_login)
# app.config["REMEMBER_COOKIE_SAMESITE"] = "strict"
# app.config["SESSION_COOKIE_SAMESITE"] = "strict"

app.register_blueprint(error)
app.register_blueprint(api)
app.register_blueprint(user)
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

