from flask import render_template, redirect, url_for, flash, request
from app import db
from app.auth import bp
from flask_login import login_user, logout_user, current_user
from werkzeug.urls import url_parse
from app.auth.forms import LoginForm, RegistrationForm
from app.models import User

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
		next_page = request.args.get('next')
		if not next_page or url_parse(next_page).netloc != '':
			next_page = url_for('main.ShowIndex')
		return redirect(next_page)
	return render_template ('auth/login.html', form = form)

@bp.route('/register/', methods = ['GET', 'POST'])
def PerformRegistration():
	if current_user.is_authenticated:
		return redirect(url_for('main.ShowIndex'))
	form = RegistrationForm()
	if form.validate_on_submit():
		email = form.email.data.lower()
		user = User(email = email)
		user.SetPassword(form.password.data)		
		db.session.add(user)
		db.session.commit()
		flash ('Теперь вы можете войти.')
		return redirect(url_for('auth.PerformLogin'))
	return render_template ('auth/register.html', form = form)

@bp.route('/logout/')
def PerformLogout():
	logout_user()
	return redirect(url_for('auth.PerformLogin'))