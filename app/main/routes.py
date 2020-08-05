from app import db
from flask_login import current_user, login_required
from app.main import bp
from app.models import User, UserRoles, Ecwid, OrderComment, OrderApproval
from flask import render_template, redirect, url_for, flash, request
from app.main.forms import EcwidSettingsForm, UserRolesForm, UserSettingsForm, OrderCommentsForm, OrderApprovalForm
from sqlalchemy import or_
from datetime import datetime, timedelta


'''
################################################################################
Index page
################################################################################
'''

def GetDateTimestamps():
	now = datetime.now()
	today = datetime(now.year, now.month, now.day)
	week = today - timedelta(days = today.weekday())
	month = datetime(now.year, now.month, 1)
	dates = [int(today.timestamp()), int(week.timestamp()), int(month.timestamp())]
	return dates
	
def GetOrderStatus(order_id):
	not_approved = OrderApproval.query.filter(OrderApproval.order_id == order_id, OrderApproval.product_id != None).count() > 0
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
	if current_user.role == UserRoles.default:
		return render_template('errors/403.html'),403
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

@bp.route('/settings/', methods=['GET'])
@login_required
def ShowSettings():
	if current_user.role == UserRoles.default:
		return render_template('errors/403.html'),403
	elif current_user.role == UserRoles.admin:
		return ShowSettingsAdmin()
	else:
		return ShowSettingsUser()
		
@bp.route('/settings/', methods=['POST'])
@login_required
def SaveSettings():
	if current_user.role == UserRoles.admin:
		ecwid_form = EcwidSettingsForm()
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
			return redirect(url_for('main.ShowSettings'))
		role_form = UserRolesForm()
		users = User.query.filter(or_(User.role == UserRoles.default, User.ecwid_id == current_user.ecwid_id)).all()
		role_form.user_id.choices = [(u.id, '{} ({})'.format(u.email, str(u.role))) for u in users]
		if role_form.validate_on_submit() and role_form.submit2.data:
			user = User.query.filter(User.id == role_form.user_id.data).first()
			if user:
				user.ecwid_id = current_user.ecwid_id
				user.role = UserRoles(role_form.role.data)
				user.phone = role_form.phone.data.strip()
				user.name = role_form.name.data.strip()
				user.location = role_form.location.data.strip()
				db.session.commit()
				flash('Данные успешно сохранены.')
			else:
				flash('Пользователь не найден.')
	else:
		user_form = UserSettingsForm()
		if user_form.validate_on_submit() and user_form.submit3.data:
			current_user.phone = user_form.phone.data.strip()
			current_user.name = user_form.name.data.strip()
			current_user.location = user_form.location.data.strip()
			db.session.commit()
			flash('Данные успешно сохранены.')
	return redirect(url_for('main.ShowSettings'))
	
def ShowSettingsAdmin():
	if not current_user.ecwid:
		ecwid = Ecwid()
		current_user.ecwid = ecwid
		db.session.commit()
	ecwid_form = EcwidSettingsForm(partners_key = current_user.ecwid.partners_key,
						client_id = current_user.ecwid.client_id,
						client_secret = current_user.ecwid.client_secret,
						store_id = current_user.ecwid.store_id)
	role_form = UserRolesForm()
	users = User.query.filter(or_(User.role == UserRoles.default, User.ecwid_id == current_user.ecwid_id)).all()
	role_form.user_id.choices = [(u.id, u.email) for u in users if u.id != current_user.id]
	return render_template('settings.html', ecwid_form = ecwid_form, role_form = role_form, users = users)
	
def ShowSettingsUser():
	user_form = UserSettingsForm(name = current_user.name, phone = current_user.phone, location = current_user.location)
	return render_template('settings.html', user_form = user_form)

'''
################################################################################
Approve page
################################################################################
'''

@bp.route('/order/<int:order_id>')
@login_required
def ShowOrder(order_id):
	if current_user.role == UserRoles.default:
		return render_template('errors/403.html'),403
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
	comments = OrderComment.query.join(User).filter(OrderComment.order_id == order_id, User.ecwid_id == current_user.ecwid_id).all()
	comment = OrderComment.query.filter(OrderComment.order_id == order_id, OrderComment.user_id == current_user.id).first()
	approvals = OrderApproval.query.join(User).filter(OrderApproval.order_id == order_id, User.ecwid_id == current_user.ecwid_id).all()
	current_approvals = OrderApproval.query.filter(OrderApproval.order_id == order_id, OrderApproval.user_id == current_user.id).all()
	if comment:
		comment_form = OrderCommentsForm(comment = comment.comment)
	else:
		comment_form = OrderCommentsForm()
	for product in order['items']:
		product['approval'] = GetProductStatus(order_id, product['productId'], current_user.id)
	order['approval'] = not GetProductStatus(order_id, None, current_user.id)
	approval_form = OrderApprovalForm()
	return render_template('approve.html',
							order = order,
							comments = comments,
							approvals = approvals,
							comment_form = comment_form,
							approval_form = approval_form)
	
@bp.route('/comment/<int:order_id>', methods=['POST'])
@login_required
def SaveComment(order_id):
	if current_user.role not in [UserRoles.validator, UserRoles.approver, UserRoles.initiative]:
		return render_template('errors/403.html'),403
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
def SaveApproval(order_id):
	if current_user.role not in [UserRoles.validator, UserRoles.approver]:
		return render_template('errors/403.html'),403
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
def DeleteOrder(order_id):
	try:
		json = current_user.ecwid.EcwidGetStoreOrders(orderNumber = order_id)
		if not 'items' in json or len(json['items']) == 0:
			raise Exception('Такой заявки не существует.')
		order = json['items'][0]
		if current_user.email != order['email']:
			raise Exception('Вы не являетесь владельцем этой заявки.')
		OrderApproval.query.join(User).filter(OrderApproval.order_id == order_id, User.ecwid_id == current_user.ecwid_id).delete()
		OrderComment.query.join(User).filter(OrderComment.order_id == order_id, User.ecwid_id == current_user.ecwid_id).delete()
		json = current_user.ecwid.EcwidDeleteStoreOrder(order_id = order_id)
		if json.get('deleteCount', default = 0, type = int) == 1:
			flash('Заявка успешно удалена')
		else:
			raise Exception('Не удалось удалить заявку.')
	except Exception as e:
		flash('Ошибка API: {}'.format(e))
	return redirect(url_for('main.ShowIndex'))
	