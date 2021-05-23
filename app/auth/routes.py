from flask import render_template, redirect, url_for, flash, request
from app import db
from app.auth import bp
from flask_login import login_user, logout_user, current_user
from werkzeug.urls import url_parse
from app.auth.forms import LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm
from app.models import User, UserRoles
from app.auth.email import SendPasswordResetEmail, SendUserRegisteredEmail
from flask import current_app

from datetime import datetime, timezone

@bp.route('/login/', methods = ['GET', 'POST'])
def PerformLogin():
	if current_user.is_authenticated:
		return redirect(url_for('main.ShowIndex'))
	form = LoginForm()
	if form.validate_on_submit():
		email = form.email.data.lower()
		user = User.query.filter_by(email = email).first()
		if user is None or not user.CheckPassword(form.password.data):
			flash('Некорректный логин или пароль')
			return redirect(url_for('auth.PerformLogin'))
		login_user(user, remember=form.remember_me.data)
		current_app.logger.info('{} logged'.format(user.email))
		user.last_logon = datetime.now(tz = timezone.utc)
		db.session.commit()
		if current_user.role == UserRoles.initiative:
			return redirect(url_for('main.ShowEcwid'))
		else:
			return redirect(url_for('main.ShowIndex'))
	return render_template ('auth/login.html', form = form)

@bp.route('/register/', methods = ['GET', 'POST'])
def PerformRegistration():
	if current_user.is_authenticated and current_user.role != UserRoles.admin:
		return redirect(url_for('main.ShowIndex'))
	form = RegistrationForm()
	if form.validate_on_submit():
		email = form.email.data.lower()
		user = User(email = email)
		user.SetPassword(form.password.data)
		db.session.add(user)
		db.session.commit()
		SendUserRegisteredEmail(user)
		flash ('Теперь пользователь может войти.')
		current_app.logger.info('{} registered'.format(user.email))
		if current_user.is_authenticated and current_user.role == UserRoles.admin:
			return redirect(url_for('main.ShowSettings'))
		else:
			return redirect(url_for('auth.PerformLogin'))
	return render_template ('auth/register.html', form = form)

@bp.route('/logout/')
def PerformLogout():
	logout_user()
	return redirect(url_for('auth.PerformLogin'))
	
@bp.route('/request/', methods=['GET', 'POST'])
def RequestPaswordReset():
	if current_user.is_authenticated:
		return redirect(url_for('main.ShowIndex'))
	form = ResetPasswordRequestForm()
	if form.validate_on_submit():
		email = form.email.data.lower()
		user = User.query.filter_by(email=email).first()
		if user:
			SendPasswordResetEmail(user)
			flash('На вашу электронную почту отправлен запрос на сброс пароля.')
			return redirect(url_for('auth.PerformLogin'))
		else:
			flash('Такой пользователь не обнаружен.')
	return render_template('auth/request.html', form = form)
	
@bp.route('/reset/<token>', methods=['GET', 'POST'])
def ResetPassword(token):
	if current_user.is_authenticated:
		return redirect(url_for('main.ShowIndex'))
	user = User.VerifyPasswordResetToken(token)
	if not user:
		return redirect(url_for('main.ShowIndex'))
	form = ResetPasswordForm()
	if form.validate_on_submit():
		user.SetPassword(form.password.data)
		db.session.commit()
		flash('Ваш пароль был изменён.')
		return redirect(url_for('auth.PerformLogin'))
	return render_template('auth/reset.html', form=form)