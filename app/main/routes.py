from app import db
from flask_login import current_user, login_required
from app.main import bp
from app.models import User, UserRoles, Ecwid, OrderComment, OrderApproval
from flask import render_template, redirect, url_for, flash, request, jsonify
from app.main.forms import EcwidSettingsForm, UserRolesForm, UserSettingsForm, OrderCommentsForm, OrderApprovalForm, ChangeQuantityForm
from sqlalchemy import or_
from datetime import datetime, timedelta
from functools import wraps

'''
################################################################################
Index page
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
				return jsonify({'status':False, 'flash':['У вас нет соответствующих полномочий.']})
			else:
				return function(*args, **kwargs)
		return wrapper
	return decorator

def GetDateTimestamps():
	now = datetime.now()
	today = datetime(now.year, now.month, now.day)
	week = today - timedelta(days = today.weekday())
	month = datetime(now.year, now.month, 1)
	dates = [int(today.timestamp()), int(week.timestamp()), int(month.timestamp())]
	return dates
	
def GetOrderStatus(order_id):
	not_approved = OrderApproval.query.join(User).filter(OrderApproval.order_id == order_id, OrderApproval.product_id != None, User.ecwid_id == current_user.ecwid_id).count() > 0
	if not_approved:
		return 'not_approved'
	approved = OrderApproval.query.join(User).filter(OrderApproval.order_id == order_id, OrderApproval.product_id == None, User.role == UserRoles.approver, User.ecwid_id == current_user.ecwid_id).count()
	approvers = User.query.filter(User.role == UserRoles.approver, User.ecwid_id == current_user.ecwid_id).count()
	if approved == 0:
		return 'new'
	elif approved == approvers:
		return 'approved'
	return 'partly_approved'
	
def GetProductStatus(order_id, product_id, user_id):
	return OrderApproval.query.filter(OrderApproval.order_id == order_id, OrderApproval.product_id == product_id, OrderApproval.user_id == user_id).count() == 0

@bp.route('/')
@bp.route('/index/')
@login_required
@role_required([UserRoles.initiative, UserRoles.validator, UserRoles.approver, UserRoles.admin])
def ShowIndex():
	dates = GetDateTimestamps()
	created_from = request.args.get('created_from', default = None, type = int)
	order_approval = request.args.get('order_approval', default = None, type = str)
	location = request.args.get('location', default = None, type = str)
	if order_approval not in ['approved', 'partly_approved', 'not_approved', 'new']:
		order_approval = None
	try:
		created_from = datetime.fromtimestamp(created_from)
		created_from = int(created_from.timestamp())
	except:
		created_from = None
	orders = []
	if current_user.ecwid:
		try:
			args = {}
			if created_from:
				args['createdFrom'] = created_from
			if current_user.role == UserRoles.initiative:
				args['email'] = current_user.email
			else:
				if location:
					args['email'] = location
			json = current_user.ecwid.EcwidGetStoreOrders(**args)
			if 'items' in json:
				orders = json['items']
		except Exception as e:
			flash('Ошибка API: {}'.format(e))
			flash('Возможно неверные настройки?')
		new_orders = []
		initiatives = {}
		for order in orders:
			initiative = User.query.filter(User.email == order['email'].lower()).first()
			if not initiative:
				continue
			order['createDate'] = datetime.strptime(order['createDate'], '%Y-%m-%d %H:%M:%S %z')
			order['approval'] = GetOrderStatus(order['orderNumber'])
			if order_approval and order['approval'] != order_approval:
				continue
			if not initiative.email in initiatives:
				if initiative.location and initiative.location != '':
					initiatives[initiative.email] = initiative.location
				else:
					initiatives[initiative.email] = order['orderComments']
			new_orders.append(order)
		orders = new_orders
	else:
		flash('Взаимодействие с ECWID не настроено.')
	return render_template('index.html', orders = orders, dates = dates,
							created_from = created_from, order_approval = order_approval,
							initiatives = initiatives,
							location = location)

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
		if not current_user.ecwid:
			ecwid = Ecwid()
			current_user.ecwid = ecwid
			db.session.commit()
		ecwid_form = EcwidSettingsForm()
		role_form = UserRolesForm()
		users = User.query.filter(or_(User.role == UserRoles.default, User.ecwid_id == current_user.ecwid_id)).all()
		role_form.user_id.choices = [(u.id, u.email) for u in users if u.id != current_user.id]
		if ecwid_form.validate_on_submit() and ecwid_form.submit1.data:
			current_user.ecwid.partners_key = ecwid_form.partners_key.data
			current_user.ecwid.client_id = ecwid_form.client_id.data
			current_user.ecwid.client_secret = ecwid_form.client_secret.data
			current_user.ecwid.store_id = ecwid_form.store_id.data
			try:
				current_user.ecwid.EcwidGetStoreToken()
				db.session.commit()
				flash('Данные успешно сохранены.')
			except Exception as e:
				flash('Ошибка GetStoreToken: {}'.format(e))
		elif role_form.validate_on_submit() and role_form.submit2.data:
			ecwid_form = EcwidSettingsForm()
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
		if user_form.validate_on_submit() and user_form.submit3.data:
			current_user.phone = user_form.about_user.phone.data.strip()
			current_user.name = user_form.about_user.full_name.data.strip()
			current_user.location = user_form.about_user.location.data.strip()
			db.session.commit()
			flash('Данные успешно сохранены.')
		return render_template('settings.html', user_form = user_form)
		
'''
################################################################################
Approve page
################################################################################
'''

@bp.route('/order/<int:order_id>')
@login_required
@role_required([UserRoles.initiative, UserRoles.validator, UserRoles.approver, UserRoles.admin])
def ShowOrder(order_id):
	try:
		json = current_user.ecwid.EcwidGetStoreOrders(orderNumber = order_id)
		if not 'items' in json or len(json['items']) == 0:
			raise Exception('Такой заявки не существует.')
	except Exception as e:
		flash('Ошибка API: {}'.format(e))
		return redirect(url_for('main.ShowIndex'))
	order = json['items'][0]
	if current_user.role == UserRoles.initiative:
		if order['email'].lower() != current_user.email:
				flash('Эта заявка не ваша.')
				return redirect(url_for('main.ShowIndex'))
		order['approval'] = GetOrderStatus(order['orderNumber'])
	elif current_user.role in [UserRoles.validator, UserRoles.approver]:
		for product in order['items']:
			product['approval'] = GetProductStatus(order_id, product['productId'], current_user.id)
		if current_user.role == UserRoles.approver:
			order['approval'] = not GetProductStatus(order_id, None, current_user.id)
		
	order['createDate'] = datetime.strptime(order['createDate'], '%Y-%m-%d %H:%M:%S %z')
	comments = OrderComment.query.join(User).filter(OrderComment.order_id == order_id, User.ecwid_id == current_user.ecwid_id).all()
	approvals = OrderApproval.query.join(User).filter(OrderApproval.order_id == order_id, User.ecwid_id == current_user.ecwid_id).all()
	approval_form = OrderApprovalForm()
	quantity_form = ChangeQuantityForm()
	comment_form = OrderCommentsForm()
	return render_template('approve.html',
							order = order,
							comments = comments,
							approvals = approvals,
							comment_form = comment_form,
							approval_form = approval_form,
							quantity_form = quantity_form)
	
@bp.route('/comment/<int:order_id>', methods=['POST'])
@login_required
@role_required([UserRoles.initiative, UserRoles.validator, UserRoles.approver])
def SaveComment(order_id):
	form = OrderCommentsForm()
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
		db.session.commit()
	return redirect(url_for('main.ShowOrder', order_id = order_id))
	
@bp.route('/approval/<int:order_id>', methods=['POST'])
@login_required
@role_required([UserRoles.validator, UserRoles.approver])
def SaveApproval(order_id):
	form = OrderApprovalForm()
	if form.validate_on_submit():
		order_approval = OrderApproval.query.filter(OrderApproval.order_id == order_id, OrderApproval.user_id == current_user.id, OrderApproval.product_id == None).first()
		if not form.product_id.data:
			if current_user.role == UserRoles.validator:
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
def DeleteOrder(order_id):
	try:
		json = current_user.ecwid.EcwidGetStoreOrders(orderNumber = order_id)
		if not 'items' in json or len(json['items']) == 0:
			raise Exception('Такой заявки не существует.')
		order = json['items'][0]
		if current_user.email != order['email']:
			raise Exception('Вы не являетесь владельцем этой заявки.')
		json = current_user.ecwid.EcwidDeleteStoreOrder(order_id = order_id)
		if json.get('deleteCount', 0) == 1:
			OrderApproval.query.join(User).filter(OrderApproval.order_id == order_id, User.ecwid_id == current_user.ecwid_id).delete()
			OrderComment.query.join(User).filter(OrderComment.order_id == order_id, User.ecwid_id == current_user.ecwid_id).delete()
			flash('Заявка успешно удалена')
		else:
			raise Exception('Не удалось удалить заявку.')
	except Exception as e:
		flash('Ошибка API: {}'.format(e))
	return redirect(url_for('main.ShowIndex'))
	
@bp.route('/quantity/<int:order_id>', methods=['POST'])
@login_required
@role_required_ajax([UserRoles.initiative])
def SaveQuantity(order_id):
	flash_messages = list()
	status = False
	new_total = ''
	form = ChangeQuantityForm()
	if form.validate_on_submit():
		try:
			json = current_user.ecwid.EcwidGetStoreOrders(orderNumber = order_id)
			if not 'items' in json or len(json['items']) == 0:
				raise Exception('Такой заявки не существует.')
			order = json['items'][0]
			for product in order['items']:
				if form.product_id.data == product['productId']:
					order['total'] += (form.product_quantity.data - product['quantity'])*product['price']
					if order['total'] < 0:
						order['total'] = 0
					new_total = '{:,.2f}'.format(order['total'])
					product['quantity'] = form.product_quantity.data
					break
			json = current_user.ecwid.EcwidUpdateStoreOrder(order_id, order)
			if json.get('updateCount', 0) == 1:
				flash_messages.append('Количество {} было изменено в заявке {}'.format(product['sku'], order_id))
				status = True
			else:
				raise Exception('Не удалось изменить заявку.')
		except Exception as e:
			flash_messages.append('Ошибка API: {}'.format(e))
			flash_messages.append('Не удалось изменить количество.')
	else:
		for error in form.product_id.errors + form.product_quantity.errors:
			flash_messages.append(error)
	return jsonify({'status':status, 'flash':flash_messages, 'total':new_total})