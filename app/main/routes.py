from app import db
from flask_login import current_user, login_required
from app.main import bp
from app.models import User, UserRoles, Ecwid, OrderComment, OrderApproval, OrderStatus
from flask import render_template, redirect, url_for, flash, request, jsonify
from app.main.forms import EcwidSettingsForm, UserRolesForm, UserSettingsForm, OrderCommentsForm, OrderApprovalForm, ChangeQuantityForm, AddStoreForm
from sqlalchemy import or_
from datetime import datetime, timedelta
from functools import wraps
from app.ecwid import EcwidAPIException
import subprocess

'''
################################################################################
Utilities
################################################################################
'''

def role_required(roles_list):
	def decorator(function):
		@wraps(function)
		def wrapper(*args, **kwargs):
			if current_user.role not in roles_list:
				return render_template('errors/403.html'),403
			else:
				return function(*args, **kwargs)
		return wrapper
	return decorator
	
def role_required_ajax(roles_list):
	def decorator(function):
		@wraps(function)
		def wrapper(*args, **kwargs):
			if current_user.role not in roles_list:
				return jsonify({'status':False, 'flash':['У вас нет соответствующих полномочий.']}),403
			else:
				return function(*args, **kwargs)
		return wrapper
	return decorator
	

def ecwid_required(function):
	@wraps(function)
	def wrapper(*args, **kwargs):
		if not current_user.hub:
			flash('Взаимодействие с ECWID не настроено.')
			return render_template('errors/400.html'),400
		else:
			return function(*args, **kwargs)
	return wrapper

def ecwid_required_ajax(function):
	@wraps(function)
	def wrapper(*args, **kwargs):
		if not current_user.hub:
			return jsonify({'status':False, 'flash':['Взаимодействие с ECWID не настроено.']}),400
		else:
			return function(*args, **kwargs)
	return wrapper
	
def GetDateTimestamps():
	now = datetime.now()
	today = datetime(now.year, now.month, now.day)
	week = today - timedelta(days = today.weekday())
	month = datetime(now.year, now.month, 1)
	dates = [int(today.timestamp()), int(week.timestamp()), int(month.timestamp())]
	return dates
	
def GetOrderStatus(order):
	if order['externalFulfillment']:
		return OrderStatus.sent
	order_id = order['orderNumber']
	not_approved = OrderApproval.query.join(User).filter(OrderApproval.order_id == order_id, OrderApproval.product_id != None, User.ecwid_id == current_user.ecwid_id).count() > 0
	if not_approved:
		return OrderStatus.not_approved
	approved = OrderApproval.query.join(User).filter(OrderApproval.order_id == order_id, OrderApproval.product_id == None, User.role == UserRoles.approver, User.ecwid_id == current_user.ecwid_id).count()
	approvers = User.query.filter(User.role == UserRoles.approver, User.ecwid_id == current_user.ecwid_id).count()
	comments = OrderComment.query.join(User).filter(OrderComment.order_id == order_id, User.ecwid_id == current_user.ecwid_id).count()
	if approved == 0 and comments == 0:
		return OrderStatus.new
	elif approved == approvers:
		return OrderStatus.approved
	return OrderStatus.partly_approved
	
def GetProductStatus(order_id, product_id, user_id):
	'''
		Returns current user order status if product_id is None
	'''
	return OrderApproval.query.filter(OrderApproval.order_id == order_id, OrderApproval.product_id == product_id, OrderApproval.user_id == user_id).count() == 0

'''
################################################################################
Index page
################################################################################
'''

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
	if filter_approval not in [str(status) for status in OrderStatus]:
		filter_approval = None
	try:
		filter_from = datetime.fromtimestamp(filter_from)
		filter_from = int(filter_from.timestamp())
	except:
		filter_from = None
		
	orders = []
	initiatives = {}

	try:
		args = {}
		if filter_from:
			args['createdFrom'] = filter_from
		if current_user.role == UserRoles.initiative:
			args['email'] = current_user.email
		else:
			if filter_location:
				args['email'] = filter_location
		json = current_user.hub.EcwidGetStoreOrders(**args)
		if 'items' in json:
			orders = json['items']
	except EcwidAPIException as e:
		flash('Ошибка API: {}'.format(e))
		flash('Возможно неверные настройки?')

	new_orders = []
	for order in orders:
		order_email = order['email'].lower()
		if not order_email in initiatives:
			initiative = User.query.filter(User.email == order_email, User.role == UserRoles.initiative).first()
			if not initiative:
				continue
			if initiative.location and initiative.location != '':
				initiatives[order_email] = initiative.location
			else:
				initiatives[order_email] = order_email
		order['initiative'] = initiatives[order_email]
		if len(order['orderComments']) > 50:
			order['orderComments'] = order['orderComments'][:50] + '...'
		order['createDate'] = datetime.strptime(order['createDate'], '%Y-%m-%d %H:%M:%S %z')
		order['status'] = str(GetOrderStatus(order))
		if filter_approval and order['status'] != filter_approval:
			continue
		new_orders.append(order)
	orders = new_orders

	return render_template('index.html',
							orders = orders, dates = dates, initiatives = initiatives,
							filter_from = filter_from,
							filter_approval = filter_approval,
							filter_location = filter_location)

'''
################################################################################
Settings page
################################################################################
'''

@bp.route('/settings/', methods=['GET', 'POST'])
@login_required
@role_required([UserRoles.initiative, UserRoles.validator, UserRoles.approver, UserRoles.admin])
def ShowSettings():
	if current_user.role == UserRoles.admin:
		if not current_user.hub:
			current_user.hub = Ecwid()
			db.session.commit()
		ecwid_form = EcwidSettingsForm()
		role_form = UserRolesForm()
		users = User.query.filter(or_(User.role == UserRoles.default, User.ecwid_id == current_user.ecwid_id)).all()
		role_form.user_id.choices = [(u.id, u.email) for u in users if u.id != current_user.id]
		if ecwid_form.submit1.data and ecwid_form.validate_on_submit():
			current_user.hub.partners_key = ecwid_form.partners_key.data
			current_user.hub.client_id = ecwid_form.client_id.data
			current_user.hub.client_secret = ecwid_form.client_secret.data
			current_user.hub.store_id = ecwid_form.store_id.data
			current_user.hub.ecwid_id = None
			try:
				current_user.hub.EcwidGetStoreToken()
				db.session.commit()
				flash('Данные успешно сохранены.')
			except:
				db.session.rollback()
				flash('Ошибка API или магазин уже используется.')
				flash('Возможно неверные настройки?')
		elif role_form.submit2.data and role_form.validate_on_submit():
			user = User.query.filter(User.id == role_form.user_id.data).first()
			if user:
				user.ecwid_id = current_user.ecwid_id
				user.role = UserRoles(role_form.role.data)
				user.phone = role_form.about_user.phone.data.strip()
				user.name = role_form.about_user.full_name.data.strip()
				user.location = role_form.about_user.location.data.strip()
				db.session.commit()
				flash('Данные успешно сохранены.')
			else:
				flash('Пользователь не найден.')
		return render_template('settings.html', ecwid_form = ecwid_form, role_form = role_form, users = users)
	else:
		user_form = UserSettingsForm()
		if user_form.validate_on_submit():
			current_user.phone = user_form.about_user.phone.data.strip()
			current_user.name = user_form.about_user.full_name.data.strip()
			current_user.location = user_form.about_user.location.data.strip()
			db.session.commit()
			flash('Данные успешно сохранены.')
		return render_template('settings.html', user_form = user_form)

@bp.route('/remove/<int:user_id>')
@login_required
@role_required([UserRoles.admin])
def RemoveUser(user_id):
	user = User.query.filter(User.id == user_id, or_(User.role == UserRoles.default, User.ecwid_id == current_user.ecwid_id)).first()
	if not user:
		flash('Пользователь не найден.')
		return redirect(url_for('main.ShowSettings'))
	OrderApproval.query.filter(OrderApproval.user_id == user_id).delete()
	OrderComment.query.filter(OrderComment.user_id == user_id).delete()
	db.session.delete(user)
	db.session.commit()
	flash('Пользователь успешно удалён.')
	return redirect(url_for('main.ShowSettings'))
	
	
'''
################################################################################
Stores page
################################################################################
'''
@bp.route('/stores/', methods=['GET', 'POST'])
@login_required
@role_required([UserRoles.initiative, UserRoles.validator, UserRoles.approver, UserRoles.admin])
@ecwid_required
def ShowStores():
	store_form = AddStoreForm()
	if current_user.role == UserRoles.admin:
		if store_form.validate_on_submit():
			try:
				store_name = store_form.name.data.strip()
				store_email = store_form.email.data.strip().lower()
				store_id = current_user.hub.EcwidCreateStore(name = store_name, email = store_email, password = store_form.password.data, plan = store_form.plan.data,
																defaultlanguage='ru')
				store = Ecwid(store_id = store_id, ecwid_id = current_user.ecwid_id, partners_key = current_user.hub.partners_key,
								client_id = current_user.hub.client_id, client_secret = current_user.hub.client_secret)
				db.session.add(store)
				store.EcwidGetStoreToken()
				store.EcwidUpdateStoreProfile({'settings':{'storeName':store_name}, 'company':{'companyName':store_name, 'city':'Москва', 'countryCode':'RU'}})
				db.session.commit()
				flash('Магазин успешно добавлен.')
			except EcwidAPIException as e:
				db.session.rollback()
				flash('Ошибка API или магазин уже используется.')
				flash('Возможно неверные настройки?')
	vendors = Ecwid.query.filter(Ecwid.ecwid_id == current_user.ecwid_id).all()
	stores = list()
	for vendor in vendors:
		try:
			stores.append(vendor.EcwidGetStoreProfile())
		except EcwidAPIException as e:
			flash('Ошибка API: {}'.format(e))
	if len(stores) == 0:
		flash('Ни один поставщик не зарегистрован в системе.')
	return render_template('stores.html', store_form = store_form, stores = stores)
	
	
@bp.route('/withdraw/<int:store_id>')
@login_required
@role_required([UserRoles.admin])
@ecwid_required
def WithdrawStore(store_id):
	store = Ecwid.query.filter(Ecwid.store_id == store_id, Ecwid.ecwid_id == current_user.ecwid_id).first()
	if store:
		try:
			store.EcwidDeleteStore()
		except EcwidAPIException as e:
			flash('Ошибка API: {}'.format(e))
		db.session.delete(store)
		db.session.commit()
		flash('Поставщик успешно удалён.')
	else:	
		flash('Этот поставщик не зарегистрован в системе.')
	return redirect(url_for('main.ShowStores'))
	
@bp.route('/sync/')
@login_required
@role_required([UserRoles.admin])
@ecwid_required
def SyncStores():
	args = ("c/ecwid-api", str(current_user.ecwid_id))
	popen = subprocess.Popen(args, stderr=subprocess.PIPE)
	popen.wait()
	output = popen.stderr.read()
	if output and len(output) > 0:
		for s in output.decode('utf-8').strip().split('\n'):
			flash(s)
	else:
		flash('Синхронизация успешно завершена.')
	return redirect(url_for('main.ShowStores'))
	
	
'''
################################################################################
Approve page
################################################################################
'''

@bp.route('/order/<int:order_id>')
@login_required
@role_required([UserRoles.initiative, UserRoles.validator, UserRoles.approver, UserRoles.admin])
@ecwid_required
def ShowOrder(order_id):
	try:
		json = current_user.hub.EcwidGetStoreOrders(orderNumber = order_id)
		if 'items' not in json or len(json['items']) == 0:
			raise EcwidAPIException('Такой заявки не существует.')
		order = json['items'][0]
		order_email = order['email'].lower()
		owner = User.query.filter(User.email == order_email).first()
		if not owner:
			raise EcwidAPIException('Заявка не принадлежит ни одному из инициаторов.')
		if current_user.role == UserRoles.initiative:
			if order_email != current_user.email:
				raise EcwidAPIException('Вы не являетесь владельцем этой заявки.')
	except EcwidAPIException as e:
		flash('Ошибка API: {}'.format(e))
		return redirect(url_for('main.ShowIndex'))
		
	order['status'] = str(GetOrderStatus(order))
	if current_user.role in [UserRoles.validator, UserRoles.approver]:
		for product in order['items']:
			product['approval'] = GetProductStatus(order_id, product['productId'], current_user.id)
		if current_user.role == UserRoles.approver:
			order['approval'] = not GetProductStatus(order_id, None, current_user.id)
			
	order['createDate'] = datetime.strptime(order['createDate'], '%Y-%m-%d %H:%M:%S %z')
	order['initiative'] = owner.location if owner.location and owner.location != '' else order_email
	if len(order['orderComments']) > 50:
		order['orderComments'] = order['orderComments'][:50] + '...'
		
	comments = OrderComment.query.join(User).filter(OrderComment.order_id == order_id, User.ecwid_id == current_user.ecwid_id).all()
	user_comment = OrderComment.query.filter(OrderComment.order_id == order_id, OrderComment.user_id == current_user.id).first()
	approvals = OrderApproval.query.join(User).filter(OrderApproval.order_id == order_id, User.ecwid_id == current_user.ecwid_id).all()
	
	approval_form = OrderApprovalForm()
	quantity_form = ChangeQuantityForm()
	comment_form = OrderCommentsForm(comment = user_comment.comment if user_comment else None)
	
	return render_template('approve.html',
							order = order,
							comments = comments,
							approvals = approvals,
							comment_form = comment_form,
							approval_form = approval_form,
							quantity_form = quantity_form)


@bp.route('/comment/<int:order_id>', methods=['POST'])
@login_required
@role_required_ajax([UserRoles.initiative, UserRoles.validator, UserRoles.approver])
def SaveComment(order_id):
	flash_messages = ['Не удалось изменить комментарий.']
	status = False
	form = OrderCommentsForm()
	stripped = ''
	if form.validate_on_submit():
		comment = OrderComment.query.filter(OrderComment.order_id == order_id, OrderComment.user_id == current_user.id).first()
		stripped = form.comment.data.strip() if form.comment.data else ''
		if len(stripped) == 0:
			if comment:
				db.session.delete(comment)
		else:
			if not comment:
				comment = OrderComment(user_id = current_user.id, order_id = order_id)
				db.session.add(comment)
			comment.comment = stripped
		status = True
		flash_messages = []
		db.session.commit()
	return jsonify({'status':status, 'flash':flash_messages, 'comment':stripped})


@bp.route('/approval/<int:order_id>', methods=['POST'])
@login_required
@role_required([UserRoles.validator, UserRoles.approver])
def SaveApproval(order_id):
	form = OrderApprovalForm()
	if form.validate_on_submit():
		order_approval = OrderApproval.query.filter(OrderApproval.order_id == order_id, OrderApproval.user_id == current_user.id, OrderApproval.product_id == None).first()
		if not form.product_id.data:
			if current_user.role != UserRoles.approver:
				return render_template('errors/403.html'),403
			OrderApproval.query.filter(OrderApproval.order_id == order_id, OrderApproval.user_id == current_user.id).delete()
			if not order_approval:
				order_approval = OrderApproval(order_id = order_id, product_id = None, user_id = current_user.id)
				db.session.add(order_approval)
		else:
			product_approval = OrderApproval.query.filter(OrderApproval.order_id == order_id, OrderApproval.user_id == current_user.id, OrderApproval.product_id == form.product_id.data).first()
			if product_approval:
				db.session.delete(product_approval)
			else:
				if order_approval:
					db.session.delete(order_approval)
				product_approval = OrderApproval(order_id = order_id, product_id = form.product_id.data, user_id = current_user.id, product_sku = form.product_sku.data.strip())
				db.session.add(product_approval)
		db.session.commit()
	return redirect(url_for('main.ShowOrder', order_id = order_id))


@bp.route('/delete/<int:order_id>')
@login_required
@role_required([UserRoles.initiative])
@ecwid_required
def DeleteOrder(order_id):
	try:
		json = current_user.hub.EcwidGetStoreOrders(orderNumber = order_id)
		if 'items' not in json or len(json['items']) == 0:
			raise EcwidAPIException('Такой заявки не существует.')
		order = json['items'][0]
		if current_user.email != order['email'].lower():
			raise EcwidAPIException('Вы не являетесь владельцем этой заявки.')
		json = current_user.hub.EcwidDeleteStoreOrder(order_id = order_id)
		OrderApproval.query.filter(OrderApproval.order_id == order_id, OrderApproval.user_id == current_user.id).delete()
		OrderComment.query.filter(OrderComment.order_id == order_id, OrderComment.user_id == current_user.id).delete()
		flash('Заявка успешно удалена')
	except EcwidAPIException as e:
		flash('Ошибка API: {}'.format(e))
	return redirect(url_for('main.ShowIndex'))


@bp.route('/quantity/<int:order_id>', methods=['POST'])
@login_required
@role_required_ajax([UserRoles.initiative])
@ecwid_required_ajax
def SaveQuantity(order_id):
	flash_messages = list()
	status = False
	new_total = ''
	form = ChangeQuantityForm()
	if form.validate_on_submit():
		try:
			json = current_user.hub.EcwidGetStoreOrders(orderNumber = order_id)
			if 'items' not in json or len(json['items']) == 0:
				raise EcwidAPIException('Такой заявки не существует.')
			order = json['items'][0]
			if current_user.email != order['email'].lower():
				raise EcwidAPIException('Вы не являетесь автором заявки.')
			for product in order['items']:
				if form.product_id.data == product['productId']:
					order['total'] += (form.product_quantity.data - product['quantity'])*product['price']
					if order['total'] < 0:
						order['total'] = 0
					new_total = '{:,.2f}'.format(order['total'])
					product['quantity'] = form.product_quantity.data
					break
			json = current_user.hub.EcwidUpdateStoreOrder(order_id, order)
			flash_messages.append('Количество {} было изменено в заявке.'.format(product['sku']))
			status = True
		except EcwidAPIException as e:
			flash_messages.append('Ошибка API: {}'.format(e))
			flash_messages.append('Не удалось изменить количество.')
	else:
		for error in form.product_id.errors + form.product_quantity.errors:
			flash_messages.append(error)
	return jsonify({'status':status, 'flash':flash_messages, 'total':new_total})

	
@bp.route('/process/<int:order_id>')
@login_required
@role_required([UserRoles.approver])
@ecwid_required
def ProcessHubOrder(order_id):

	_DISALLOWED_ORDERS_ITEM_FIELDS = ['productId', 'id', 'categoryId']
	_DISALLOWED_ORDERS_FIELDS = ['vendorOrderNumber', 'customerId', 'privateAdminNotes', 'externalFulfillment']
	try:
		json = current_user.hub.EcwidGetStoreOrders(orderNumber = order_id)
		if 'items' not in json or len(json['items']) == 0:
			raise EcwidAPIException('Такой заявки не существует.')
	except EcwidAPIException as e:
		flash('Ошибка API: {}'.format(e))
		return redirect(url_for('main.ShowIndex'))

	order = json['items'][0]
	
	for key in _DISALLOWED_ORDERS_FIELDS:
		order.pop(key, None)
	for product in order['items']:
		for key in _DISALLOWED_ORDERS_ITEM_FIELDS:
			product.pop(key, None)
			
	stores = Ecwid.query.filter(Ecwid.ecwid_id == current_user.ecwid_id).all()
	got_orders = {}
	for store in stores:
		products = list()
		total = 0
		for product in order['items']:
			try:
				dash = product['sku'].index('-')
			except ValueError:
				continue
			if product['sku'][:dash] == str(store.store_id):
				product_new = product.copy()
				product_new['sku'] = product_new['sku'][dash+1:]
				products.append(product_new)
				total += product_new['price'] * product_new['quantity']
		if len(products) == 0:
			continue
		items = order['items']
		order['items'] = products
		order['subtotal'] = total
		order['total'] = total
		order['email'] = current_user.email
		result = store.EcwidSetStoreOrder(order)
		if 'id' not in result:
			flash('Не удалось отправить заявку поставщику {}.'.format(store.store_id))
		else:
			try:
				profile = store.EcwidGetStoreProfile()
				got_orders[profile['account']['accountName']] = result['id']
			except:
				got_orders[store.store_id] = result['id']
		order['items'] = items

	if len(got_orders) > 0:
		vendor_str = ', '.join(f'{vendor}: #{order}' for vendor,order in got_orders.items())
		try:
			current_user.hub.EcwidUpdateStoreOrder(order_id, {'privateAdminNotes':vendor_str, 'externalFulfillment':True})
		except EcwidAPIException as e:
			flash('Ошибка API: {}'.format(e))
			flash('Не удалось сохранить информацию о передаче поставщикам.')
		flash('Заявка была отправлена поставщикам: {}.'.format(vendor_str))
	else:
		flash('Не удалось перезаказать данные товары у зарегистрованных поставщиков.')

	return redirect(url_for('main.ShowOrder', order_id = order_id))