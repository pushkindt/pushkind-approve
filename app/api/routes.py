from app.api import bp
from flask import jsonify, g, current_app, render_template
from app.api.auth import basic_auth
from app import db
from app.api.errors import BadRequest, ErrorResponse
from datetime import datetime, timedelta, timezone
from app.models import User, UserRoles, ApiData, CacheCategories
from app.ecwid import EcwidAPIException
from app.email import SendEmail
from app.main.utils import GetReviewersEmails


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
		json = user.hub.EcwidGetStoreOrders(createdFrom=int(api_data.timestamp.timestamp()))
		orders = json.get('items', [])
	except EcwidAPIException as e:
		return ErrorResponse(503)
	api_data.timestamp = datetime.now(tz = timezone.utc)
	db.session.commit()
	
	initiatives = User.query.filter(User.ecwid_id == user.ecwid_id, User.role == UserRoles.initiative).all()
	initiatives = {k.email:k for k in initiatives}
	for order in orders:
		order['email'] = order['email'].lower()
		if order['email'] not in initiatives:
			continue
		order['initiative'] = initiatives[order['email']]
		emails = GetReviewersEmails(order)
		SendEmail('Новая заявка #{}'.format(order['vendorOrderNumber']),
				   sender=current_app.config['MAIL_USERNAME'],
				   recipients=emails,
				   text_body=render_template('email/new.txt', order=order),
				   html_body=render_template('email/new.html', order=order),
				   sync=True)
	return jsonify({'result':'success'})