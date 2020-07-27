from flask import current_app
from flask_httpauth import HTTPBasicAuth
from app.api.errors import ErrorResponse
from flask import g
from app.models import User

basic_auth = HTTPBasicAuth()

@basic_auth.verify_password
def verify_password(email, password):
	user = User.query.filter_by(email=email).first()
	if user is None:
			return False
	g.user_id = user.id
	return user.CheckPassword(password)

@basic_auth.error_handler
def basic_auth_error():
	return ErrorResponse(401)