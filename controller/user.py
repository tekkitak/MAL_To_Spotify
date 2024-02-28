from flask import Blueprint, render_template_string, current_app as app, redirect
from model.database import db
from flask_security.utils      import hash_password
from flask_security.decorators import auth_required
from flask_security            import current_user


user = Blueprint(
    'user',
    __name__,
    template_folder='templates/user',
    url_prefix='/user'
)


@user.route('/cradmin')
def cradmin():
    if not app.security.datastore.find_user(email="test@me.com"):
        app.security.datastore.create_user(
                email="test@me.com",
                password=hash_password("password"),
                username="Admin",
                e=True
        )
        db.session.commit()
        return 'Success'
    return 'Already exists'


@user.route('/test')
@auth_required()
def test():
    page = """
    Hello {{ current_user.username }}
    <br>
    Roles:
    <ul>
    {% for role in current_user.roles%}
        <li>{{role.name}}</li>
    {% endfor %}
    </ul>
    """
    return render_template_string(page)


@user.route('/profile')
@auth_required()
def profile() -> None:
    pass
