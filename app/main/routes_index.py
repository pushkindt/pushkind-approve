from app import db
from flask_login import current_user, login_required
from app.main import bp
from app.models import User, UserRoles, OrderStatus
from flask import render_template, flash, request
from sqlalchemy import distinct, func
from app.ecwid import EcwidAPIException
from app.main.utils import DATE_TIME_FORMAT, role_required, ecwid_required, GetOrderStatus
from datetime import datetime, timedelta, timezone


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
@role_required([UserRoles.initiative, UserRoles.validator, UserRoles.approver, UserRoles.admin])
@ecwid_required
def ShowIndex():
	dates = GetDateTimestamps()
	filter_from = request.args.get('from', default = None, type = int)
	filter_approval = request.args.get('approval', default = None, type = str)
	filter_location = request.args.get('location', default = None, type = str)
	if filter_approval not in [status.name for status in OrderStatus]:
		filter_approval = None
	locations = db.session.query(distinct(func.lower(User.location))).filter(User.ecwid_id == current_user.ecwid_id, User.role == UserRoles.initiative).all()
	
	if current_user.role == UserRoles.initiative:
		initiatives = [current_user]
	else:
		if filter_location != None:
			initiatives = User.query.filter(User.ecwid_id == current_user.ecwid_id, User.role == UserRoles.initiative, User.location.ilike(filter_location.strip())).all()
		else:
			initiatives = User.query.filter(User.ecwid_id == current_user.ecwid_id, User.role == UserRoles.initiative).all()

	initiatives = {k.email:k for k in initiatives}

	orders = []

	args = {}
	if filter_from:
		args['createdFrom'] = filter_from
		
	try:
		json = current_user.hub.EcwidGetStoreOrders(**args)
		orders = json.get('items', [])
	except EcwidAPIException as e:
		flash('Ошибка API: {}'.format(e))
	
	new_orders = []
	for order in orders:
		order['createDate'] = datetime.strptime(order['createDate'], DATE_TIME_FORMAT)
		order['updateDate'] = datetime.strptime(order['updateDate'], DATE_TIME_FORMAT)
		order['status'] = GetOrderStatus(order)
		if filter_approval and order['status'].name != filter_approval:
			continue
		if len(order['orderComments']) > 50:
			order['orderComments'] = order['orderComments'][:50] + '...'

		order['email'] = order['email'].lower()
		if order['email'] not in initiatives:
			continue
		order['initiative'] = initiatives[order['email']]
		new_orders.append(order)
	
	orders = new_orders
	return render_template('index.html',
							orders = orders, dates = dates, locations = locations,
							filter_from = filter_from,
							filter_approval = filter_approval,
							filter_location = filter_location,
							OrderStatus = OrderStatus)

