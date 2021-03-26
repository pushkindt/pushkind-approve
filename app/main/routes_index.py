from app import db
from flask_login import current_user, login_required
from app.main import bp
from app.models import UserRoles, OrderStatus, Location, EventLog, EventType
from flask import render_template, flash, request, redirect, url_for
from app.ecwid import EcwidAPIException
from app.main.utils import ecwid_required, PrepareOrder, role_forbidden, ProcessOrderComments, ORDER_COMMENTS_FIELDS
from datetime import datetime, timedelta, timezone
from app.main.forms import MergeOrdersForm
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
	if current_user.role not in [UserRoles.approver, UserRoles.validator]:
		locations = [loc.name for loc in Location.query.order_by(Location.name).all()]
	else:
		try:
			locations = current_user.data['locations']
		except (TypeError,KeyError):
			locations = []

	orders = []
	args = {}
	if filter_from is not None:
		args['createdFrom'] = filter_from
	if filter_location is not None:
		filter_location = filter_location.strip()
		args['refererId'] = filter_location
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
		if current_user.role in [UserRoles.validator, UserRoles.approver]:
			if current_user.id not in reviewers:
				continue
		if filter_approval and order['status'].name != filter_approval:
			continue
		new_orders.append(order)
	
	orders = new_orders
	form = MergeOrdersForm()
	return render_template('index.html',
							orders = orders, dates = dates, locations = locations,
							filter_from = filter_from,
							filter_approval = filter_approval,
							filter_location = filter_location,
							OrderStatus = OrderStatus,
							form = form)


@bp.route('/merge/', methods=['POST'])
@login_required
@role_forbidden([UserRoles.default])
@ecwid_required
def MergeOrders():
	form = MergeOrdersForm()
	if form.validate_on_submit():
		try:
			orders_list = json.loads(form.orders.data)
			if not isinstance(orders_list, list) or len(orders_list) == 0:	
				raise ValueError
		except (JSONDecodeError, ValueError):
			flash('Некорректный список заявок.')
			return redirect(url_for('main.ShowIndex'))
			
		orders = list()
		try:
			for order_id in orders_list:
				response = current_user.hub.GetStoreOrders(orderNumber = order_id)
				if 'items' not in response or len(response['items']) != 1:
					raise EcwidAPIException(f'Заявка {order_id} не найдена.')
				order = response['items'][0]
				
				order['orderComments'] = ProcessOrderComments(order.get('orderComments', ''))
				orders.append(order)
				if order.get('refererId', '') != orders[0].get('refererId', ''):
					raise EcwidAPIException('Нельзя объединять заявки от разных площадок.')
					
				if all([order['orderComments'][k] == orders[0]['orderComments'][k] for k in ORDER_COMMENTS_FIELDS[1:]]) is False:
					raise EcwidAPIException('Нельзя объединять заявки с разными полями БДР, БДДС, Объект.')
					
		except EcwidAPIException as e:
			flash('Ошибка API: {}'.format(e))
			return redirect(url_for('main.ShowIndex'))
		
		products = dict()
		for order in orders:
			for product in order['items']:
				if len(product['selectedOptions']) > 1:
					product_id = product['sku'] + ''.join(sorted([k['value'] for k in product['selectedOptions']]))
				else:
					product_id = product['sku']
				if product_id not in products:
					products[product_id] = dict()
					products[product_id]['sku'] = product['sku']
					products[product_id]['name'] = product['name']
					products[product_id]['price'] = product['price']
					products[product_id]['quantity'] = product['quantity']
					products[product_id]['productPrice'] = product['productPrice']
					products[product_id]['selectedOptions'] = product['selectedOptions']
					products[product_id]['categoryId'] = product['categoryId']
				else:
					products[product_id]['quantity'] += product['quantity']
					products[product_id]['price'] += product['price']
		order = dict()
		order['email'] = current_user.email
		order['items'] = [products[sku] for sku in products.keys()]
		order['paymentStatus'] = 'AWAITING_PAYMENT'
		order['fulfillmentStatus'] = 'AWAITING_PROCESSING'
		order['total'] = sum([product['quantity']*product['price'] for product in order['items']])
		order['refererId'] = orders[0].get('refererId', '')
		order['orderComments'] = json.dumps(orders[0]['orderComments'])

		try:
			response = current_user.hub.SetStoreOrder(order)
			if 'id' not in response:
				raise EcwidAPIException('Не удалось создать заявку.')
		except EcwidAPIException:
			flash('Ошибка API: {}'.format(e))
			return redirect(url_for('main.ShowIndex'))
		
		
		message = 'Заявка объединена из заявок'
		for order_id in orders_list:
			message += ' <a href={}>{}</a>'.format(url_for('main.ShowOrder', order_id = order_id), order_id)
			message2 = 'Заявка объединена в заявку <a href={}>{}</a>'.format(url_for('main.ShowOrder', order_id = response['id']), response['id'])
			event = EventLog(user_id = current_user.id, order_id = order_id, type=EventType.duplicated, data=message2, timestamp = datetime.now(tz = timezone.utc))
			db.session.add(event)
			
		event = EventLog(user_id = current_user.id, order_id = response['id'], type=EventType.duplicated, data=message, timestamp = datetime.now(tz = timezone.utc))
		db.session.add(event)
		
		db.session.commit()
		
		flash(f'Объединено заявок: {len(orders)}. Идентификатор новой заявки {response["id"]}')
	else:
		for error in form.orders.errors:
			flash(error)
	return redirect(url_for('main.ShowIndex'))