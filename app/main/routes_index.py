from app import db
from flask_login import current_user, login_required
from app.main import bp
from app.models import User, UserRoles, OrderStatus, CacheCategories, Location
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
	dates = {'сегодня':int(today.timestamp()), 'неделя':int(week.timestamp()), 'месяц':int(month.timestamp())}
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
		
	if filter_location is not None:
		filter_location = filter_location.strip()
	locations = Location.query.all()

	orders = []
	args = {}
	if filter_from is not None:
		args['createdFrom'] = filter_from
	if filter_location is not None:
		filter_location = filter_location.strip()
		args['paymentMethod'] = filter_location
	if current_user.role == UserRoles.initiative:
		args['email'] = current_user.email
	try:
		orders = current_user.hub.GetStoreOrders(**args)
		orders = orders.get('items', [])
	except EcwidAPIException as e:
		flash('Ошибка API: {}'.format(e))

	new_orders = []
	for order in orders:
		if not PrepareOrder(order):
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

