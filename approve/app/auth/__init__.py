from flask import Blueprint

bp = Blueprint('auth', __name__)

from approve.app.auth import routes
