from app import db
from flask_login import current_user, login_required
from app.main import bp
from app.models import User, UserRoles, OrderStatus, CacheCategories
from flask import render_template, flash, request
from sqlalchemy import distinct, func, or_
from app.ecwid import EcwidAPIException
from app.main.utils import DATE_TIME_FORMAT, role_required, ecwid_required, PrepareOrder, role_forbidden
from datetime import datetime, timedelta, timezone
import json
from json.decoder import JSONDecodeError

'''
################################################################################
Index page
################################################################################
'''

def GetDateTimestamps():
	now = datetime.now(tz = timezone.utc)
	today = datetime(now.year, now.month, now.day)
	week = today - timedelta(days = today.weekday())
	month = datetime(now.year, now.month, 1)
	dates = [int(today.timestamp()), int(week.timestamp()), int(month.timestamp())]
	return dates

@bp.route('/')
@bp.route('/index/')
@login_required
@role_forbidden([UserRoles.default])
@ecwid_required
def ShowIndex():
	dates = GetDateTimestamps()
	filter_from = request.args.get('from', default = None, type = int)
	filter_approval = request.args.get('approval', default = None, type = str)
	filter_location = request.args.get('location', default=None, type=str)

	if filter_approval not in [status.name for status in OrderStatus]:
		filter_approval = None
	if current_user.role == UserRoles.initiative:
		initiatives = [current_user]
		locations = [current_user.location]
		filter_location = None
	else:
		if filter_location != None:
			filter_location = filter_location.strip()
		locations = [loc[0] for loc in db.session.query(distinct(func.lower(User.location))).filter(User.ecwid_id == current_user.ecwid_id, User.role == UserRoles.initiative).all()]

	orders = []
	args = {}
	if filter_from:
		args['createdFrom'] = filter_from
	try:
		orders = current_user.hub.EcwidGetStoreOrders(**args)
		orders = orders.get('items', [])
	except EcwidAPIException as e:
		flash('Ошибка API: {}'.format(e))
	

	new_orders = []
	for order in orders:
		if current_user.role == UserRoles.initiative and order['email'] != current_user.email:
			continue
		if not PrepareOrder(order, filter_location):
			continue
		reviewers = [rev.id for rev in order['reviewers']]
		if current_user.role == UserRoles.validator:
			if current_user.id not in reviewers:
				continue
		if filter_approval and order['status'].name != filter_approval:
			continue
		new_orders.append(order)
	
	orders = new_orders
	return render_template('index.html',
							orders = orders, dates = dates, locations = locations,
							filter_from = filter_from,
							filter_approval = filter_approval,
							filter_location = filter_location,
							OrderStatus = OrderStatus)

