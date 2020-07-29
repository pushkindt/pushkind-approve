from app import db
from flask_login import current_user, login_required
from app.main import bp
from app.models import User, UserRoles, Ecwid
from flask import render_template, redirect, url_for, flash, request
from app.main.forms import EcwidSettingsForm, UserRolesForm, UserSettingsForm
from sqlalchemy import or_

@bp.route('/')
@bp.route('/index/')
@login_required
def ShowIndex():
	if current_user.role == UserRoles.default:
		return render_template('errors/403.html'),403
	elif current_user.role == UserRoles.initiative:
		return ShowIndexInitiative()
	else:
		return ShowIndexAdmin()
		
def ShowIndexAdmin():
	orders = None
	if current_user.ecwid:
		try:
			orders = current_user.ecwid.EcwidGetStoreOrders(limit = 3)
		except Exception as e:
			flash('Ошибка API: {}'.format(e))
			flash('Возможно неверные настройки?')
	else:
		flash('Взаимодействие с ECWID не настроено.')
	return render_template('index.html', orders = orders)
	
def ShowIndexInitiative():
	try:
		orders = current_user.ecwid.EcwidGetStoreOrders(limit = 3)
	except Exception as e:
		flash('Ошибка API: {}'.format(e))
		flash('Возможно неверные настройки?')
		orders = None
	return render_template('index.html', orders = orders)

@bp.route('/settings/', methods=['GET'])
@login_required
def ShowSettings():
	if current_user.role == UserRoles.default:
		return render_template('errors/403.html'),403
	elif current_user.role == UserRoles.admin:
		return ShowSettingsAdmin()
	else:
		return ShowSettingsUser()
		
@bp.route('/settings/', methods=['POST'])
@login_required
def SaveSettings():
	if current_user.role == UserRoles.admin:
		ecwid_form = EcwidSettingsForm()
		if ecwid_form.validate_on_submit() and ecwid_form.submit1.data:
			current_user.ecwid.partners_key = ecwid_form.partners_key.data
			current_user.ecwid.client_id = ecwid_form.client_id.data
			current_user.ecwid.client_secret = ecwid_form.client_secret.data
			current_user.ecwid.store_id = ecwid_form.store_id.data
			try:
				current_user.ecwid.EcwidGetStoreToken()
				db.session.commit()
				flash('Данные успешно сохранены.')
			except Exception as e:
				flash('Ошибка GetStoreToken: {}'.format(e))
			return redirect(url_for('main.ShowSettings'))
		role_form = UserRolesForm()
		users = User.query.filter(or_(User.role == UserRoles.default, User.ecwid_id == current_user.ecwid_id)).all()
		role_form.user_id.choices = [(u.id, '{} ({})'.format(u.email, str(u.role))) for u in users]
		if role_form.validate_on_submit() and role_form.submit2.data:
			user = User.query.filter(User.id == role_form.user_id.data).first()
			if user:
				user.ecwid_id = current_user.ecwid_id
				user.role = UserRoles(role_form.role.data)
				db.session.commit()
				flash('Данные успешно сохранены.')
			else:
				flash('Пользователь не найден.')
	else:
		user_form = UserSettingsForm()
		if user_form.validate_on_submit() and user_form.submit3.data:
			current_user.phone = user_form.phone.data
			current_user.name = user_form.name.data
			current_user.location = user_form.name.location.data
			db.session.commit()
			flash('Данные успешно сохранены.')
	return redirect(url_for('main.ShowSettings'))
	
def ShowSettingsAdmin():
	if not current_user.ecwid:
		ecwid = Ecwid()
		current_user.ecwid = ecwid
		db.session.commit()
	ecwid_form = EcwidSettingsForm(partners_key = current_user.ecwid.partners_key,
						client_id = current_user.ecwid.client_id,
						client_secret = current_user.ecwid.client_secret,
						store_id = current_user.ecwid.store_id)
	role_form = UserRolesForm()
	users = User.query.filter(or_(User.role == UserRoles.default, User.ecwid_id == current_user.ecwid_id)).all()
	role_form.user_id.choices = [(u.id, '{} ({})'.format(u.email, str(u.role))) for u in users if u.id != current_user.id]
	return render_template('settings.html', ecwid_form = ecwid_form, role_form = role_form)
	
def ShowSettingsUser():
	user_form = UserSettingsForm(name = current_user.name, phone = current_user.phone, location = current_user.location)
	return render_template('settings.html', user_form = user_form)