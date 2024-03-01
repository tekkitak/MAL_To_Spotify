from flask import Blueprint, render_template
from flask_security.decorators import permissions_required
from model.database import User, Role

admin = Blueprint(
    "admin", __name__, template_folder="templates/admin", url_prefix="/admin"
)


@admin.route("/users")
@permissions_required("user-manage")
def users():
    return render_template("admin/users.j2")


@admin.route("/users/<int:id>")
@permissions_required("user-manage")
def user(id):
    u = User.query.get(id)
    # get all roles with true/false if user has role
    r = Role.query.all()
    for role in r:
        role.user_has = role in u.roles

    return render_template("admin/user.j2", user=u, roles=r)
