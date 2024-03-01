"""This module contains the user blueprint and edpoints for the application."""

from flask import (
    Blueprint,
    current_app as app,
    redirect,
    url_for,
    request,
    render_template,
)
from flask_login import current_user
from flask_security.signals import user_registered
from flask_security.decorators import auth_required
from flask_security.utils import hash_password

from model.database import db, User


user = Blueprint("user", __name__, template_folder="templates/user", url_prefix="/user")


@user.route("/cradmin")
def cradmin() -> str:
    """Creates an admin user for testing purposes."""
    if not app.security.datastore.find_user(email="test@me.com"):
        adminUser = app.security.datastore.create_user(
            email="test@me.com",
            password=hash_password("password"),
            username="Admin",
            active=True,
        )
        app.security.datastore.add_role_to_user(adminUser, "admin")
        app.security.datastore.commit()
        return "Success"
    return "Already exists"


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

    db.session.commit()

    return redirect(url_for("user.profile"))
