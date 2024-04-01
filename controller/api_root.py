from flask import Blueprint, session, current_app
from .api.spotify import spotify
from .api.mal import mal
from .api.suggestions import suggestions
from .api.admin import admin
from .api.statistics import statistics

api = Blueprint("api", __name__, template_folder="templates/api", url_prefix="/api")

api.register_blueprint(spotify)
api.register_blueprint(mal)
api.register_blueprint(suggestions)
api.register_blueprint(admin)
api.register_blueprint(statistics)


@api.route("/clear")
def SessionClear():
    if current_app.config["ENV"] != "development":
        return " "
    session.clear()
    return "Cleared"
