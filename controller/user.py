from flask import Blueprint, render_template_string, current_app as app, redirect, url_for, request, render_template
from model.database import db, User
from flask_security import user_registered, auth_required, hash_password, current_user
from crypt import methods
from flask.helpers import redirect, url_for


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
def profile():
    return render_template('user/profile.j2')


@user_registered.connect_via(user)
def user_registered_sighandler(**args) -> None:
    print(user)


@user.route('/delete_account')
@auth_required()
def delete_account():
    db.session.delete(current_user)
    return redirect(url_for('security.logout'))


@user.route('/edit_profile', methods=['POST'])
@auth_required()
def edit_profile():
    print(dir(request))
    data: dict[str, str] = request.form
    if not 'user_id' in data:
        return 'No user id provided', 400
    if int(data['user_id']) != int(current_user.id):
        print(data['user_id'])
        print(current_user.id)
        return 'Unauthorized', 401
    c_user: User | None = User.query.filter_by(id=data['user_id']).first()
    if c_user is None:
        return 'User not found', 404
    if 'username' in data:
        c_user.username = data['username']
    if 'email' in data:
        c_user.email = data['email']

    db.session.commit()

    return redirect(url_for('user.profile'))
