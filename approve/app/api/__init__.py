from flask import Blueprint

bp = Blueprint('api', __name__)

from approve.app.api import routes, errors
