from json import dumps
from flask import Blueprint, request, redirect, url_for
from flask_security.decorators import permissions_required
from model.database import User, Role, db

admin = Blueprint('admin', __name__,
                    template_folder='templates/admin',
                    url_prefix='/admin')

@admin.route('/getUsers')
@permissions_required('user-manage')
def users() -> str:
    """
    Returns a list of users

    Params:
        limit: int - The amount of users to return
        offset: int - The offset to start from

    Returns:
        json - A list of users
    """

    limit:  int = request.args.get('limit', default=10, type=int)
    offset: int = request.args.get('offset', default=0, type=int)

    user_list = User.query.limit(limit).offset(offset).all()

    output = {
        'recordsTotal': User.query.count(),
        'offset': offset,
        'limit': limit,
        'data': []
    }
    for idx, user in enumerate(user_list):
        roles = []
        for role in user.roles:
            roles.append({
                'id': role.id,
                'name': role.name,
                'description': role.description,
            })
        output['data'].append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'roles': roles,
        })

    return dumps(output)

@admin.route('/editUser', methods=['POST'])
@permissions_required('user-manage')
def edit_user():
    """
    Edit a user

    Params:
        id: int - The id of the user to edit
        username: str - The new username
        email: str - The new email
        roles: list - The new roles

    Returns:
        json - The user that was edited
    """

    id: int = request.form.get('id', type=int)
    username: str = request.form.get('username')
    email: str = request.form.get('email')

    roles = []
    for role in Role.query.all():
        if request.form.get(f'role_{role.id}'):
            roles.append(role)


    user = User.query.get(id)
    user.username = username
    user.email = email
    user.roles = roles

    db.session.commit()

    return redirect(url_for('admin.users'))
