from flask import render_template, request
from app import db
from app.errors import bp
from app.api.errors import ErrorResponse


def WantsJsonResponse():
	return request.accept_mimetypes['application/json'] >= \
		request.accept_mimetypes['text/html']


@bp.app_errorhandler(404)
def NotFoundError(error):
	if WantsJsonResponse():
		return ErrorResponse(404)
	return render_template('errors/404.html'), 404
	
@bp.app_errorhandler(403)
def NotFoundError(error):
	if WantsJsonResponse():
		return ErrorResponse(403)
	return render_template('errors/403.html'), 403


@bp.app_errorhandler(500)
def InternalError(error):
	db.session.rollback()
	if WantsJsonResponse():
		return ErrorResponse(500)
	return render_template('errors/500.html'), 500