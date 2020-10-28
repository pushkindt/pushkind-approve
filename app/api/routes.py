from app.api import bp
from flask import jsonify, g, current_app, render_template
from app.api.auth import basic_auth
from app import db
from app.api.errors import BadRequest, ErrorResponse
from datetime import datetime, timedelta, timezone
from app.models import User, UserRoles, ApiData, CacheCategories
from app.ecwid import EcwidAPIException
from app.main.utils import PrepareOrder, SendEmailNotification


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
		return ErrorResponse(503)
	api_data.timestamp = datetime.now(tz = timezone.utc)
	db.session.commit()
	
	initiatives = User.query.filter(User.ecwid_id == user.ecwid_id, User.role == UserRoles.initiative).all()
	initiatives = {k.email:k for k in initiatives}
	for order in orders:
		if not PrepareOrder(order):
			continue
		SendEmailNotification('new', order)
	return jsonify({'result':'success'})