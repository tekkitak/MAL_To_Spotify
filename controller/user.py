from flask import Blueprint, render_template_string, current_app as app
from model.database import db
from flask_security.utils      import hash_password
from flask_security.signals    import user_registered
from flask_security.decorators import auth_required


user = Blueprint(
    'user',
    __name__,
    template_folder='templates/user',
    url_prefix='/user'
)


@user.route('/cradmin')
def cradmin():
    if not app.security.datastore.find_user(email="test@me.com"):
        app.security.datastore.create_user(email="test@me.com",
                                           password=hash_password("password"),
                                           username="Admin",
                                           active=True)
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


@user_registered.connect_via(user)
def user_registered_sighandler(**args) -> None:
    print(f"User created\targs: {args=}")
