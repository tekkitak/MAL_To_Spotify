from flask import Blueprint, render_template

error = Blueprint("error", __name__, template_folder="templates/error")


@error.app_errorhandler(404)
def page_not_found(error: Exception):
    return render_template("error/404.j2"), 404
