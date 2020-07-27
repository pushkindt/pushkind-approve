from app import db
from flask_login import current_user, login_required
from app.main import bp
from app.models import User
from flask import render_template, redirect, url_for, flash, request


@bp.route('/')
@bp.route('/index/')
@login_required
def ShowIndex():
	return render_template('index.html')