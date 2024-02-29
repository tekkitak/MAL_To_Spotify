from flask import Blueprint, render_template
from flask_security.decorators import permissions_required

admin = Blueprint('admin', __name__,
                    template_folder='templates/admin',
                    url_prefix='/admin')

@admin.route('/users')
@permissions_required('user-manage')
def users():
    return render_template('admin/users.j2')