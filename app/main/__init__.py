from datetime import datetime

from flask import Blueprint, request, session
from flask_login import current_user

from app import db

bp = Blueprint("main", __name__)


@bp.before_app_request
def before_request():
    if request.endpoint == "auth.login_token":
        return
    if session.pop("skip_last_seen_once", False):
        return
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


from app.main import (
    routes_admin,
    routes_approve,
    routes_dashboard,
    routes_help,
    routes_history,
    routes_index,
    routes_limits,
    routes_products,
    routes_settings,
    routes_shop,
    routes_stores,
)
