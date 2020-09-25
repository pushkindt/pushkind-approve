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


def GetReviewersEmails(order):
	approvers = User.query.filter(User.role == UserRoles.approver, User.ecwid_id == order['initiative'].ecwid_id).all()
	validators = User.query.filter(User.role == UserRoles.validator, User.ecwid_id == order['initiative'].ecwid_id).all()
	emails = [approver.email for approver in approvers]
	for validator in validators:
		try:
			filter_validator = json.loads(validator.location)
		except JSONDecodeError:
			emails.append(validator.email)
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
			emails.append(validator.email)
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
			emails.append(validator.email)
	return list(set(emails))
		
		