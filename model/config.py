from os import getenv


def set_config(app) -> None:
    """Funnction that sets config object for app"""

    app.config.update({
        'SECRET_KEY': getenv('FLASK_SECRET_KEY'),

        'SESSION_PERMANENT': False,
        'SESSION_TYPE': 'filesystem',

        'SECURITY_PASSWORD_SALT': getenv('SECURITY_PASSWORD_SALT'),
        'SECURITY_BLUEPRINT_NAME': 'security',
        'SECURITY_STATIC_FOLDER': 'security',
        'SECURITY_REGISTERABLE': True,
        'SECURITY_SEND_REGISTER_EMAIL': False,
        'SECURITY_EMAIL_SENDER': None,
        'SECURITY_USERNAME_ENABLE': True,
        'SECURITY_USERNAME_REQUIRED': True,
        "SECURITY_CONFIRMABLE": False,
        "SECURITY_RECOVERABLE": True,
        "SECURITY_WAN_ALLOW_AS_FIRST_FACTOR": True,

        "SQLALCHEMY_ENGINE_OPTIONS": {
            "pool_pre_ping": True,
            },
        'SQLALCHEMY_DATABASE_URI': getenv('DATABASE_URL'),
        "SQLALCHEMY_TRACK_MODIFICATIONS": False
    })

