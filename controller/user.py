"""This module contains the user blueprint and edpoints for the application."""
from flask import (
    Blueprint,
    redirect,
    url_for,
    request,
    render_template,
    session,
)
from flask_login import current_user
from flask_security.signals import user_registered
from flask_security.decorators import auth_required, anonymous_user_required

from model.database import db, User, OAuth2
from model.oauth_login import register_auto_login, unregister_auto_login, auto_login, oauth_data


user = Blueprint("user", __name__, template_folder="templates/user", url_prefix="/user")


@user.route("/profile")
@auth_required()
def profile() -> str:
    """Returns the profile page for the user"""
    return render_template("user/profile.j2")


@user_registered.connect_via(user)
def user_registered_sighandler(**args) -> None:
    """Handles the user_registered signal"""
    print(user)


@user.route("/delete_account")
@auth_required()
def delete_account():
    """Deletes the account of the current user and logs them out."""
    c_user = User.query.filter_by(id=current_user.id).first()
    db.session.delete(c_user)
    db.session.commit()
    return redirect(url_for("security.logout"))


@user.route("/edit_profile", methods=["POST"])
@auth_required()
def edit_profile():
    """
    Edits the profile of the current user.
    This is a POST request that takes the following parameters:
    - user_id: The id of the user to edit
    - username: The new username
    - email: The new email
    """
    print(dir(request))
    data: dict[str, str] = request.form
    if "user_id" not in data:
        return "No user id provided", 400
    if int(data["user_id"]) != int(current_user.id):
        print(data["user_id"])
        print(current_user.id)
        return "Unauthorized", 401
    c_user: User | None = User.query.filter_by(id=data["user_id"]).first()
    if c_user is None:
        return "User not found", 404

    if "username" in data:
        c_user.username = data["username"]
    if "email" in data:
        c_user.email = data["email"]

    for provider in oauth_data.keys():
        if f"{provider}-switch" in data:
            OAuth2.query.filter_by(provider=provider, user=current_user).first().allow_login = True
            register_auto_login(provider, session[provider].get_Bearer())
        else:
            try:
                unregister_auto_login(provider)
            except Exception:
                pass
    db.session.commit()

    return redirect(url_for("user.profile"))


@user.route("/check_oauth_login")
@anonymous_user_required
def check_oauth_login() -> redirect:
    """Checks if the user is logged in via OAuth2"""
    for provider in oauth_data.keys():
        if provider in session:
            if auto_login(provider, session[provider].get_Bearer()) is not None:
                return redirect(url_for("user.profile"))
    return redirect(url_for("security.login"))
