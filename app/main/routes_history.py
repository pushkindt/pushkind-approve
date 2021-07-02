from app import db
from flask_login import current_user, login_required
from app.main import bp
from app.models import UserRoles, Order, OrderEvent
from flask import render_template, flash, request, redirect, url_for
from app.main.utils import ecwid_required, role_forbidden, role_required
from datetime import datetime, timedelta, timezone

'''
################################################################################
Responibility page
################################################################################
'''

@bp.route('/history/', methods=['GET', 'POST'])
@login_required
@role_forbidden([UserRoles.default])
@ecwid_required
def ShowHistory():
	now = datetime.now(tz = timezone.utc)
	filter_from = now - timedelta(days = 42)
	events = OrderEvent.query.filter(OrderEvent.timestamp > int(filter_from.timestamp())).join(Order).filter_by(hub_id = current_user.hub_id).order_by(OrderEvent.timestamp.desc()).all()
	return render_template('history.html', events = events)