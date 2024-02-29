from json import dumps
from flask import Blueprint, request
from flask_security.decorators import permissions_required
from model.database import User

admin = Blueprint('admin', __name__,
                    template_folder='templates/admin',
                    url_prefix='/admin')

@admin.route('/getUsers')
# @permissions_required('user-manage')
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