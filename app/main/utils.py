from flask_login import current_user
from app.models import User, UserRoles, OrderApproval, OrderStatus, CacheCategories, EventLog
from flask import render_template, flash, jsonify
from functools import wraps
from datetime import datetime, timedelta, timezone
from sqlalchemy import or_

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
	
def role_forbidden(roles_list):
	def decorator(function):
		@wraps(function)
		def wrapper(*args, **kwargs):
			if current_user.role in roles_list:
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
	
def role_forbidden_ajax(roles_list):
	def decorator(function):
		@wraps(function)
		def wrapper(*args, **kwargs):
			if current_user.role in roles_list:
				return jsonify({'status':False, 'flash':['У вас нет соответствующих полномочий.']}),403
			else:
				return function(*args, **kwargs)
		return wrapper
	return decorator
	

def ecwid_required(function):
	@wraps(function)
	def wrapper(*args, **kwargs):
		if current_user.hub is None:
			flash('Взаимодействие с ECWID не настроено.')
			return render_template('errors/400.html'),400
		else:
			return function(*args, **kwargs)
	return wrapper

def ecwid_required_ajax(function):
	@wraps(function)
	def wrapper(*args, **kwargs):
		if current_user.hub is None:
			return jsonify({'status':False, 'flash':['Взаимодействие с ECWID не настроено.']}),400
		else:
			return function(*args, **kwargs)
	return wrapper
	
def GetProductApproval(order_id, user):
	return OrderApproval.query.filter(OrderApproval.order_id == order_id, OrderApproval.user_id == user.id).all()


def PrepareOrder(order):
	order['initiative'] = User.query.filter(User.email == order['email'], User.role == UserRoles.initiative).first()
	if order['initiative'] is None:
		return False
	try:
		order['createDate'] = datetime.strptime(order['createDate'], DATE_TIME_FORMAT)
	except (ValueError, KeyError, TypeError):
		order['createDate'] = datetime.now()
	try:
		order['updateDate'] = datetime.strptime(order['updateDate'], DATE_TIME_FORMAT)
	except (ValueError, KeyError, TypeError):
		order['createDate'] = datetime.now()
	if len(order['orderComments']) > 50:
		order['orderComments'] = order['orderComments'][:50] + '...'
	approvers = User.query.filter(User.role == UserRoles.approver, User.ecwid_id == order['initiative'].ecwid_id).all()
	validators = User.query.filter(User.role == UserRoles.validator, User.ecwid_id == order['initiative'].ecwid_id).all()
	reviewers = {approver: GetProductApproval(order['orderNumber'], approver) for approver in approvers}
	for validator in validators:
		if not isinstance(validator.data,dict):
			continue
		try:
			locations = [loc.lower() for loc in validator.data['locations']]
			if len(locations) == 0:
				raise KeyError
		except (TypeError,KeyError):
			continue
		try:
			categories = [cat.lower() for cat in validator.data['categories']]
			if len(categories) == 0:
				raise KeyError
		except (TypeError,KeyError):
			continue
			
		caches = CacheCategories.query.filter(CacheCategories.ecwid_id == order['initiative'].ecwid_id, or_(*[CacheCategories.name.ilike(cat) for cat in categories])).all()
		categories = set([cat_id for cache in caches for cat_id in cache.children])
		product_cats = set([product.get('categoryId', None) for product in order['items']])
		check_categories = len(categories.intersection(product_cats)) > 0
		check_locations = order['paymentMethod'].lower() in locations
		if	check_locations is True and check_categories is True:
			reviewers[validator] = GetProductApproval(order['orderNumber'], validator)
	order['reviewers'] = reviewers
	order['events'] = EventLog.query.join(User).filter(EventLog.order_id == order['orderNumber'], User.ecwid_id == order['initiative'].ecwid_id).order_by(EventLog.timestamp.desc()).all()
	not_approved = OrderApproval.query.join(User).filter(OrderApproval.order_id == order['orderNumber'], OrderApproval.product_id != None, User.ecwid_id == order['initiative'].ecwid_id).count() > 0
	if not_approved is True:
		order['status'] = OrderStatus.not_approved
		return True

	approvals = {}
	for reviewer,status in order['reviewers'].items():
		if reviewer.role == UserRoles.validator:
			position = reviewer.position.lower()
			approvals[position] = approvals.get(position, False) or any(status)
			
	if all(approvals.values()) and len(approvals) > 0:
		order['status'] = OrderStatus.approved
		return True
	if len(order['events']) > 0:
		order['status'] = OrderStatus.partly_approved
		return True
	if (order['updateDate'] - order['createDate']) > timedelta(seconds=10):
		order['status'] = OrderStatus.modified
		return True
	order['status'] = OrderStatus.new
	return True