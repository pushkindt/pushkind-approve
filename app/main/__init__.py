from flask import Blueprint

bp = Blueprint('main', __name__)

from app.main import routes_index
from app.main import routes_approve
from app.main import routes_settings
from app.main import routes_stores
from app.main import routes_buyer