from flask import render_template
from flask_login import login_required, current_user

from approve.app.main import bp
from approve.app.models import UserRoles, Project, OrderLimit
from approve.app.main.utils import role_required


@bp.route('/buyer/')
@login_required
@role_required([UserRoles.initiative, UserRoles.purchaser, UserRoles.admin])
def ShowEcwid():
    projects = Project.query
    if current_user.role != UserRoles.admin:
        projects = projects.filter_by(enabled=True)
    projects = projects.filter_by(hub_id=current_user.hub_id)
    projects = projects.order_by(Project.name).all()
    limits = OrderLimit.query.filter_by(hub_id=current_user.hub_id).all()
    return render_template('buyer.html', projects=projects, limits=limits)
