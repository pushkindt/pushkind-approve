from flask import Blueprint
from flask_login import current_user
from approve.app import db
from datetime import datetime

bp = Blueprint('main', __name__)

@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

from approve.app.main import routes_index
from approve.app.main import routes_approve
from approve.app.main import routes_settings
from approve.app.main import routes_stores
from approve.app.main import routes_buyer
from approve.app.main import routes_help
from approve.app.main import routes_history
from approve.app.main import routes_admin
from approve.app.main import routes_limits