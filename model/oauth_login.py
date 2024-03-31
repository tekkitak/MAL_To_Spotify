import requests as rq
from flask_security.decorators import auth_required
from flask_security import current_user, login_user
from model.database import db, OAuth2, User
from typing import Optional


oauth_data: dict[str, dict] = {
    "spotify_oauth": {
        "url": "https://api.spotify.com/v1/me",
        "id_get": lambda json: json["id"]
    },
    "mal_oauth": {
        "url": "https://api.myanimelist.net/v2/users/@me",
        "id_get": lambda json: json["id"]
    },
}


def _get_id(provider: str, auth_header: str) -> str:
    """Gets id from api of given provider"""
    if provider not in oauth_data:
        raise Exception("Provider not found")
    cur_oauth = oauth_data[provider]

    response = rq.get(cur_oauth["url"], headers={"Authorization": auth_header})
    if response.status_code != 200:
        raise Exception("Invalid Authorization")
    return cur_oauth["id_get"](response.json())


@auth_required()
def register_auto_login(provider: str, auth_header: str) -> None:
    """Registers the auto login process"""
    user_id = _get_id(provider, auth_header)

    if OAuth2.query.filter_by(provider_user_id=user_id).first() is not None:
        raise Exception("OAuth2 already registered under some user")

    oa = OAuth2.query.filter_by(provider=provider, user=current_user).first()
    if oa is None:
        raise Exception("Provider not found for current user")
    oa.provider_user_id = user_id
    db.session.commit()


@auth_required()
def unregister_auto_login(provider: str) -> None:
    """Unregisters the auto login process"""
    oa = OAuth2.query.filter_by(provider=provider, user=current_user).first()
    if oa is None:
        raise Exception("Provider not found for current user")
    oa.provider_user_id = None
    oa.allow_login = False
    db.session.commit()


def auto_login(provider: str, auth_header: str) -> Optional[User]:
    """Tries to login user with oauth2, returns logged in user"""
    if current_user.is_authenticated:
        return current_user
    user_id = _get_id(provider, auth_header)

    oa = OAuth2.query.filter_by(provider_user_id=user_id).first()
    if oa is not None:
        if not login_user(oa.user):
            raise Exception("Error logging in")
        return current_user
    return None
