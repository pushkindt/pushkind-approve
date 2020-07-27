from app.api import bp
from flask import jsonify, request, Response, g
from app.api.auth import basic_auth
from app import db
from app.api.errors import BadRequest
from datetime import datetime
from app.models import User
from requests import get

@bp.route('/user/', methods=['GET'])
@basic_auth.login_required
def GetCurrentUser():
	user = User.query.get_or_404(g.user_id)
	return jsonify(user.to_dict())