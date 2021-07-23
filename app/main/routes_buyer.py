from app import db
from flask_login import login_required, current_user
from app.main import bp
from app.models import UserRoles, Project
from flask import render_template
from app.main.utils import role_required


@bp.route('/buyer/')
@login_required
@role_required([UserRoles.initiative, UserRoles.purchaser, UserRoles.admin])
def ShowEcwid():
    projects = Project.query
    if current_user.role != UserRoles.admin:
        projects = projects.filter_by(enabled=True)
    projects = projects.filter_by(hub_id=current_user.hub_id)
    projects = projects.order_by(Project.name).all()
    return render_template('buyer.html', projects=projects)
