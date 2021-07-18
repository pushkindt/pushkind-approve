from app import db
from flask_login import current_user, login_required
from app.main import bp
from app.models import UserRoles, Order, OrderEvent, EventType
from flask import render_template, flash, request, redirect, url_for
from app.main.utils import ecwid_required, role_forbidden, role_required, GetFilterTimestamps
from datetime import datetime as dt

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
    dates = GetFilterTimestamps()
    filter_from = request.args.get('from', default=dates['недавно'], type=int)
    events = OrderEvent.query.filter(OrderEvent.timestamp > dt.fromtimestamp(filter_from))
    events = events.join(Order).filter_by(hub_id=current_user.hub_id).order_by(OrderEvent.timestamp.desc()).all()
    return render_template('history.html', events=events, EventType=EventType, filter_from=filter_from, dates=dates)
