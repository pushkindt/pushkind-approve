from flask import Blueprint

bp = Blueprint('errors', __name__)

from approve.app.errors import handlers
