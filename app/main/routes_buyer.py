from app import db
from flask_login import login_required
from app.main import bp
from app.models import UserRoles, Location
from flask import render_template
from app.main.utils import role_required

@bp.route('/buyer/')
@login_required
@role_required([UserRoles.initiative, UserRoles.admin])
def ShowEcwid():
	locations = Location.query.order_by(Location.name).all()
	return render_template('buyer.html', locations = locations)