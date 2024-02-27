from flask import Flask, render_template, url_for, session
from datetime import datetime

from model.extensions       import register_extensions
from model.actions          import register_commands
from model.config           import set_config
from model.helper_functions import refresh_auth
from model.database         import db, DB_VER
from model.version_control  import verControl
from controller.error       import error
from controller.user        import user
from controller.api_root    import api
from controller.api.spotify import spotify_playlists


# Flask setup
app = Flask(__name__)
set_config(app)
register_commands(app)
register_extensions(app)

app.register_blueprint(error)
app.register_blueprint(api)
app.register_blueprint(user)


@app.before_first_request
def check_version() -> None:
    """Checks for all the versioning done with versionControl"""

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

