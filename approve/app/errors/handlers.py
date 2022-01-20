from flask import render_template, request

from approve.app import db
from approve.app.errors import bp
from approve.app.api.errors import error_response


def wants_json_response():
    return request.accept_mimetypes['application/json'] >= \
        request.accept_mimetypes['text/html']


@bp.app_errorhandler(403)
@bp.app_errorhandler(404)
@bp.app_errorhandler(500)
def not_found_error(error):
    if error.code == 500:
        db.session.rollback()
    if wants_json_response():
        return error_response(error.code)
    return render_template(f'errors/{error.code}.html'), error.code
