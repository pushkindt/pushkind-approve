from app.api import bp
from flask import jsonify, g, current_app, render_template
from app.api.auth import basic_auth
from app import db
from app.api.errors import BadRequest, ErrorResponse
from datetime import datetime, timedelta, timezone
from app.models import User, UserRoles, ApiData, CacheCategories
from app.ecwid import EcwidAPIException
from app.main.utils import PrepareOrder, SendEmailNotification
from sqlalchemy import func, or_
from app.email import SendEmail


@bp.route('/orders/', methods=['GET'])
@basic_auth.login_required
def NotifyNewOrders():
	user = User.query.get_or_404(g.user_id)
	if user.role != UserRoles.admin:
		return ErrorResponse(403)
	api_data = ApiData.query.filter(ApiData.ecwid_id == user.ecwid_id).first()
	if not api_data:
		api_data = ApiData(ecwid_id = user.ecwid_id, timestamp = datetime.now(tz = timezone.utc))
		db.session.add(api_data)
	try:
		json = user.hub.GetStoreOrders(createdFrom=int(api_data.timestamp.timestamp()))
		orders = json.get('items', [])
	except EcwidAPIException as e:
		return ErrorResponse(500)
	api_data.timestamp = datetime.now(tz = timezone.utc)
	db.session.commit()
	
	initiatives = User.query.filter(User.ecwid_id == user.ecwid_id, User.role == UserRoles.initiative).all()
	initiatives = {k.email:k for k in initiatives}
	for order in orders:
		if not PrepareOrder(order):
			SendEmailNotification('nonexistent', order)
			continue
		SendEmailNotification('new', order)
	return jsonify({'result':'success'})
	
	
@bp.route('/waiting/', methods=['GET'])
@basic_auth.login_required
def NotifyWaitingOrders():
	user = User.query.get_or_404(g.user_id)
	if user.role != UserRoles.admin:
		return ErrorResponse(403)
	try:
		json = user.hub.GetStoreOrders(createdFrom=int((datetime.now(tz = timezone.utc) - timedelta(days = 30)).timestamp()))
		orders = json.get('items', [])
	except EcwidAPIException as e:
		return ErrorResponse(500)

	recipients = {}
	
	for order in orders:
		if not PrepareOrder(order):
			continue
		for position,status in order['positions'].items():
			if status is False:
				users = User.query.filter(User.ecwid_id == user.ecwid_id, func.lower(User.position) == position, or_(User.role == UserRoles.approver,User.role == UserRoles.validator)).all()
				for u in users:
					if not u.email in recipients:
						recipients[u.email] = list()
					recipients[u.email].append(order['vendorOrderNumber'])

	for recipient, orders in recipients.items():
		current_app.logger.info('"wating" email about orders {} has been sent to {}'.format(orders, recipient))
		SendEmail('Заявки ожидают согласования',
				   sender=current_app.config['MAIL_USERNAME'],
				   recipients=[recipient],
				   text_body=render_template('email/waiting.txt', orders=orders),
				   html_body=render_template('email/waiting.html', orders=orders))
	return jsonify({'result':'success'})
		