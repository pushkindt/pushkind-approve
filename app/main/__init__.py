from datetime import datetime

from flask import Blueprint
from flask_login import current_user

from app import db


bp = Blueprint('main', __name__)

@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

from app.main import routes_index
from app.main import routes_approve
from app.main import routes_settings
from app.main import routes_stores
from app.main import routes_buyer
from app.main import routes_help
from app.main import routes_history
from app.main import routes_admin
from app.main import routes_limits