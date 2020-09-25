from app import db
from flask_login import current_user, login_required
from app.main import bp
from app.models import User, UserRoles, OrderStatus, CacheCategories
from flask import render_template, flash, request
from sqlalchemy import distinct, func, or_
from app.ecwid import EcwidAPIException
from app.main.utils import DATE_TIME_FORMAT, role_required, ecwid_required, GetOrderStatus, role_forbidden
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
		
	categories = None
	if current_user.role == UserRoles.initiative:
		initiatives = [current_user]
		locations = [current_user.location]
	elif current_user.role == UserRoles.validator:
		filter_validator = None
		try:
			filter_validator = json.loads(current_user.location)
			locations = [loc.lower() for loc in filter_validator['locations']]
			if len(locations) == 0:
				raise KeyError
		except (JSONDecodeError,TypeError,KeyError):
			locations = [loc[0] for loc in db.session.query(distinct(func.lower(User.location))).filter(User.ecwid_id == current_user.ecwid_id, User.role == UserRoles.initiative).all()]
		
		if filter_validator:
			try:
				categories = [cat.lower() for cat in filter_validator['categories']]
				if len(categories) == 0:
					raise KeyError
				caches = CacheCategories.query.filter(CacheCategories.ecwid_id == current_user.ecwid_id, or_(*[CacheCategories.name.ilike(cat) for cat in categories])).all()
				categories = set([cat_id for cache in caches for cat_id in cache.children])
				if len(categories) == 0:
					raise KeyError
			except (TypeError,KeyError):
				categories = None

		if filter_location != None:
			initiatives = User.query.filter(User.ecwid_id == current_user.ecwid_id, User.role == UserRoles.initiative, User.location.ilike(filter_location.strip())).all()
		else:
			initiatives = User.query.filter(User.ecwid_id == current_user.ecwid_id, User.role == UserRoles.initiative, or_(*[User.location.ilike(loc) for loc in locations])).all()
	else:
		if filter_location != None:
			initiatives = User.query.filter(User.ecwid_id == current_user.ecwid_id, User.role == UserRoles.initiative, User.location.ilike(filter_location.strip())).all()
		else:
			initiatives = User.query.filter(User.ecwid_id == current_user.ecwid_id, User.role == UserRoles.initiative).all()
		locations = [loc[0] for loc in db.session.query(distinct(func.lower(User.location))).filter(User.ecwid_id == current_user.ecwid_id, User.role == UserRoles.initiative).all()]

	initiatives = {k.email:k for k in initiatives}
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
		order['email'] = order['email'].lower()
		if order['email'] not in initiatives:
			continue
		order['initiative'] = initiatives[order['email']]
		if categories != None:
			order_cat = set([product.get('categoryId', None) for product in order['items']])
			if len(categories.intersection(order_cat)) == 0:
				continue
		order['createDate'] = datetime.strptime(order['createDate'], DATE_TIME_FORMAT)
		order['updateDate'] = datetime.strptime(order['updateDate'], DATE_TIME_FORMAT)
		order['status'] = GetOrderStatus(order)
		if filter_approval and order['status'].name != filter_approval:
			continue
		if len(order['orderComments']) > 50:
			order['orderComments'] = order['orderComments'][:50] + '...'
		new_orders.append(order)
	
	orders = new_orders
	return render_template('index.html',
							orders = orders, dates = dates, locations = locations,
							filter_from = filter_from,
							filter_approval = filter_approval,
							filter_location = filter_location,
							OrderStatus = OrderStatus)

