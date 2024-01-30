from datetime import datetime

from flask import Blueprint
from flask_login import current_user

from app import db

bp = Blueprint("main", __name__)


@bp.before_app_request
def before_request():
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
