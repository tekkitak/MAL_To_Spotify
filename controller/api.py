from flask import Blueprint
from controller.api.spotify import spotify # , mall

api = Blueprint('api', __name__, 
                template_folder='templates/api', 
                url_prefix='/api')

api.register_blueprint(spotify)

@api.route('/hello')
def hello():
    return 'Hello, World!'
