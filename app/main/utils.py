from flask_login import current_user
from app.models import User, UserRoles, OrderComment, OrderApproval, OrderStatus
from flask import render_template, flash, jsonify
from functools import wraps
from datetime import datetime, timedelta, timezone
	

'''
################################################################################
Consts
################################################################################
'''
DATE_TIME_FORMAT = '%Y-%m-%d %H:%M:%S %z'

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
	
def GetOrderStatus(order):
	order_id = order['orderNumber']
	not_approved = OrderApproval.query.join(User).filter(OrderApproval.order_id == order_id, OrderApproval.product_id != None, User.ecwid_id == current_user.ecwid_id).count() > 0
	if not_approved:
		return OrderStatus.not_approved
	approved = OrderApproval.query.join(User).filter(OrderApproval.order_id == order_id, OrderApproval.product_id == None, User.role == UserRoles.approver, User.ecwid_id == current_user.ecwid_id).count()
	approvers = User.query.filter(User.role == UserRoles.approver, User.ecwid_id == current_user.ecwid_id).count()
	comments = OrderComment.query.join(User).filter(OrderComment.order_id == order_id, User.ecwid_id == current_user.ecwid_id).count()
	if approved == approvers and approvers > 0:
		return OrderStatus.approved
	if (order['updateDate'] - order['createDate']) > timedelta(seconds=10):
		return OrderStatus.modified
	if approved == 0 and comments == 0:
		return OrderStatus.new
	return OrderStatus.partly_approved	
	
def GetProductApproval(order_id, product_id, user_id):
	'''
		Returns current user order approval if product_id is None
	'''
	return OrderApproval.query.filter(OrderApproval.order_id == order_id, OrderApproval.product_id == product_id, OrderApproval.user_id == user_id).count() == 0