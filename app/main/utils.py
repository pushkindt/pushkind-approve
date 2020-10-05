from flask_login import current_user
from app.models import User, UserRoles, OrderComment, OrderApproval, OrderStatus, CacheCategories
from flask import render_template, flash, jsonify
from functools import wraps
from datetime import datetime, timedelta, timezone
import json
from sqlalchemy import or_
from json.decoder import JSONDecodeError

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
	
def GetProductApproval(order_id, user):
	return OrderApproval.query.filter(OrderApproval.order_id == order_id, OrderApproval.user_id == user.id).all()


def PrepareOrder(order, filter_location=None):
	if filter_location:
		order['initiative'] = User.query.filter(User.email == order['email'], User.location.ilike(filter_location)).first()
	else:
		order['initiative'] = User.query.filter(User.email == order['email']).first()
	if not order['initiative']:
		return False
	try:
		order['createDate'] = datetime.strptime(order['createDate'], DATE_TIME_FORMAT)
	except (ValueError, KeyError):
		pass
	try:
		order['updateDate'] = datetime.strptime(order['updateDate'], DATE_TIME_FORMAT)
	except (ValueError, KeyError):
		pass
	try:
		order['privateAdminNotes'] = datetime.strptime(order['privateAdminNotes'], DATE_TIME_FORMAT)
	except (ValueError, KeyError):
		order['privateAdminNotes'] = datetime.now()
	if len(order['orderComments']) > 50:
		order['orderComments'] = order['orderComments'][:50] + '...'
	approvers = User.query.filter(User.role == UserRoles.approver, User.ecwid_id == order['initiative'].ecwid_id).all()
	validators = User.query.filter(User.role == UserRoles.validator, User.ecwid_id == order['initiative'].ecwid_id).all()
	reviewers = {approver: GetProductApproval(order['orderNumber'], approver) for approver in approvers}
	for validator in validators:
		try:
			filter_validator = json.loads(validator.location)
		except JSONDecodeError:
			reviewers[validator] = GetProductApproval(order['orderNumber'], validator)
			continue
		try:
			locations = [loc.lower() for loc in filter_validator['locations']]
			if len(locations) == 0:
				raise KeyError
		except (TypeError,KeyError):
			locations = None
		try:
			categories = [cat.lower() for cat in filter_validator['categories']]
			if len(categories) == 0:
				raise KeyError
		except (TypeError,KeyError):
			categories = None
		if locations == None and categories == None:
			reviewers[validator] = GetProductApproval(order['orderNumber'], validator)
			continue
		if categories != None:
			caches = CacheCategories.query.filter(CacheCategories.ecwid_id == order['initiative'].ecwid_id, or_(*[CacheCategories.name.ilike(cat) for cat in categories])).all()
			categories = set([cat_id for cache in caches for cat_id in cache.children])
			product_cats = set([product.get('categoryId', None) for product in order['items']])
			check_categories = len(categories.intersection(product_cats)) > 0
		else:
			check_categories = True
		if locations != None:
			check_locations = order['initiative'].location.lower() in locations
		else:
			check_locations = True
		
		if	check_locations == True and check_categories == True:
			reviewers[validator] = GetProductApproval(order['orderNumber'], validator)
	order['reviewers'] = reviewers
	order['comments'] = OrderComment.query.join(User).filter(OrderComment.order_id == order['orderNumber'], User.ecwid_id == order['initiative'].ecwid_id).all()
	not_approved = OrderApproval.query.join(User).filter(OrderApproval.order_id == order['orderNumber'], OrderApproval.product_id != None, User.ecwid_id == order['initiative'].ecwid_id).count() > 0
	if not_approved:
		order['status'] = OrderStatus.not_approved
		return True
	approvals = [any(status) for reviewer, status in reviewers.items()]
	if all(approvals):
		order['status'] = OrderStatus.approved
		return True
	if (order['updateDate'] - order['createDate']) > timedelta(seconds=10):
		order['status'] = OrderStatus.modified
		return True
	if any(approvals) or len(order['comments']) > 0:
		order['status'] = OrderStatus.partly_approved
		return True
	order['status'] = OrderStatus.new
	return True