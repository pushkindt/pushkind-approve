from flask_login import current_user
from app.models import User, UserRoles, OrderApproval, OrderStatus, CacheCategories, EventLog, EventType
from flask import render_template, flash, jsonify
from functools import wraps
from datetime import datetime, timedelta, timezone
from sqlalchemy import or_
from app.email import SendEmail
from flask import current_app
import json
from json.decoder import JSONDecodeError

'''
################################################################################
Consts
################################################################################
'''
DATE_TIME_FORMAT = '%Y-%m-%d %H:%M:%S %z'
DATE_FORMAT = '%Y-%m-%d'

ORDER_COMMENTS_FIELDS = ['comment', 'budget', 'object', 'cashflow']

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


def ProcessOrderComments(comment):

	if isinstance(comment, dict) is False:
		try:
			comment = json.loads(comment)
			if not isinstance(comment, dict):	
				raise JSONDecodeError
		except JSONDecodeError:	
			comment = {'comment':comment, 'budget':'', 'object':'', 'cashflow':''}

	for k in ORDER_COMMENTS_FIELDS:
		if not k in comment:
			comment[k] = ''
	return comment


def PrepareOrder(order):
	order['initiative'] = User.query.filter(User.email == order['email'], or_(User.role == UserRoles.initiative, User.role == UserRoles.approver)).first()
	if order['initiative'] is None:
		return False
	if not 'refererId' in order:
		order['refererId'] = ''
	try:
		if isinstance(order['createDate'], datetime) is False:
			order['createDate'] = datetime.strptime(order['createDate'], DATE_TIME_FORMAT)
	except (ValueError, KeyError, TypeError):
		order['createDate'] = datetime.now(tz = timezone.utc)
	try:
		if isinstance(order['updateDate'], datetime) is False:
			order['updateDate'] = datetime.strptime(order['updateDate'], DATE_TIME_FORMAT)
	except (ValueError, KeyError, TypeError):
		order['updateDate'] = datetime.now(tz = timezone.utc)

	order['orderComments'] = ProcessOrderComments(order.get('orderComments', ''))
		
	users = User.query.filter(or_(User.role == UserRoles.approver,User.role == UserRoles.validator), User.ecwid_id == order['initiative'].ecwid_id).all()
	reviewers = {}
	for user in users:
		if not isinstance(user.data,dict):
			continue
		try:
			locations = [loc.lower() for loc in user.data['locations']]
			if len(locations) == 0:
				raise KeyError
		except (TypeError,KeyError):
			continue
		try:
			categories = [cat.lower() for cat in user.data['categories']]
			if len(categories) == 0:
				raise KeyError
		except (TypeError,KeyError):
			continue
			
		caches = CacheCategories.query.filter(CacheCategories.ecwid_id == order['initiative'].ecwid_id, or_(*[CacheCategories.name.ilike(cat) for cat in categories])).all()
		categories = set([cat_id for cache in caches for cat_id in cache.children])
		product_cats = set([product.get('categoryId', None) for product in order['items']])
		check_categories = len(categories.intersection(product_cats)) > 0
		check_locations = order['refererId'].lower() in locations
		if	check_locations is True and check_categories is True:
			reviewers[user] = GetProductApproval(order['orderNumber'], user)
	
	order['has_units'] = all(['selectedOptions' in product for product in order['items']])
	
	order['reviewers'] = reviewers
	order['events'] = EventLog.query.join(User).filter(EventLog.order_id == order['orderNumber'], User.ecwid_id == order['initiative'].ecwid_id).order_by(EventLog.timestamp.desc()).all()
	order['export1C'] = any([event.type == EventType.export1C for event in order['events']])
	
	approvals = {}
	for reviewer,status in order['reviewers'].items():
		if reviewer.role == UserRoles.validator:
			position = reviewer.position.lower()
			approvals[position] = approvals.get(position, False) or any(status)
	order['positions'] = approvals	
	
	not_approved = OrderApproval.query.join(User).filter(OrderApproval.order_id == order['orderNumber'], OrderApproval.product_id != None, User.ecwid_id == order['initiative'].ecwid_id).count() > 0
	if not_approved is True:
		order['status'] = OrderStatus.not_approved
		return True

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
	
def SendEmailNotification(type, order):
	recipients = [reviewer.email for reviewer in order['reviewers'] if getattr(reviewer, 'email_{}'.format(type), False) == True]
	if getattr(order['initiative'], 'email_{}'.format(type), False) == True:
		recipients.append(order['initiative'].email)
	current_app.logger.info('"{}" email about order {} has been sent to {}'.format(type, order['vendorOrderNumber'], recipients))
	if len(recipients) > 0:
		SendEmail('Уведомление по заявке #{}'.format(order['vendorOrderNumber']),
				   sender=current_app.config['MAIL_USERNAME'],
				   recipients=recipients,
				   text_body=render_template('email/{}.txt'.format(type), order=order),
				   html_body=render_template('email/{}.html'.format(type), order=order))
				   
def SendEmail1C(order, subject, data):
	recipients = ['zayavka@velesstroy.com']
	current_app.logger.info('"export1C" email about order {} has been sent to {}'.format(order['vendorOrderNumber'], recipients))
	SendEmail(subject,
			   sender=current_app.config['MAIL_USERNAME'],
			   recipients=recipients,
			   text_body=render_template('email/export1C.txt', order=order),
			   html_body=render_template('email/export1C.html', order=order),
			   attachments = [data])