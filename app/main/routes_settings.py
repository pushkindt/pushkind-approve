from app import db
from flask_login import current_user, login_required
from app.main import bp
from app.models import User, UserRoles, Ecwid, OrderApproval, CacheCategories, EventLog, Location, Site, ApiData
from flask import render_template, redirect, url_for, flash
from app.main.forms import EcwidSettingsForm, UserRolesForm, UserSettingsForm, AddRemoveLocationForm, Notify1CSettingsForm
from sqlalchemy import distinct, func, or_
from app.ecwid import EcwidAPIException
from sqlalchemy.exc import SQLAlchemyError
from app.main.utils import role_required, role_forbidden
import json
from json.decoder import JSONDecodeError

'''
################################################################################
Settings page
################################################################################
'''

def ValidateUserData(userDataStr):
	try:
		result = json.loads(userDataStr)
		if not all(k in result.keys() for k in ['locations', 'categories']):
			raise JSONDecodeError
		for key in result.keys():
			if key not in ['locations', 'categories']:
				result.pop(key)
			else:
				result[key] = list(set(result[key]))
	except (JSONDecodeError, TypeError):
		result = {'locations':[], 'categories':[]}
	return result

@bp.route('/settings/', methods=['GET', 'POST'])
@login_required
@role_forbidden([UserRoles.default])
def ShowSettings():
	locations = Location.query.filter(Location.ecwid_id == current_user.ecwid_id).order_by(Location.name).all()
	categories = CacheCategories.query.filter(CacheCategories.ecwid_id == current_user.ecwid_id).all()
	if current_user.role == UserRoles.admin:
		if current_user.hub is None:
			current_user.hub = Ecwid()
			db.session.commit()
		ecwid_form = EcwidSettingsForm()
		role_form = UserRolesForm()
		
		api_data = ApiData.query.filter_by(ecwid_id = current_user.ecwid_id).first()
		if api_data is None:
			notify1C_form = Notify1CSettingsForm()
		else:
			notify1C_form = Notify1CSettingsForm(enable = api_data.notify_1C, email = api_data.email_1C)
		users = User.query.filter(or_(User.role == UserRoles.default, User.ecwid_id == current_user.ecwid_id)).order_by(User.name, User.email).all()
		if ecwid_form.submit1.data and ecwid_form.validate_on_submit():
			current_user.hub.partners_key = ecwid_form.partners_key.data
			current_user.hub.client_id = ecwid_form.client_id.data
			current_user.hub.client_secret = ecwid_form.client_secret.data
			current_user.hub.store_id = ecwid_form.store_id.data
			try:
				current_user.hub.GetStoreToken()
				profile = current_user.hub.GetStoreProfile()
				db.session.commit()
				flash('Данные успешно сохранены.')
			except (SQLAlchemyError, EcwidAPIException):
				db.session.rollback()
				flash('Ошибка API или магазин уже используется.')
				flash('Возможно неверные настройки?')
		elif role_form.submit2.data and role_form.validate_on_submit():
			user = User.query.filter(User.id == role_form.user_id.data).first()
			if user is not None:
				user.ecwid_id = current_user.ecwid_id
				user.role = UserRoles(role_form.role.data)
				if user.role in [UserRoles.validator,UserRoles.approver] and role_form.about_user.user_data.data is not None:
					user.data = ValidateUserData(role_form.about_user.user_data.data)
				else:
					user.data = None
				if role_form.about_user.phone.data is not None:
					user.phone = role_form.about_user.phone.data.strip()
				else:
					user.phone = ''
				if role_form.about_user.position.data is not None:
					user.position = role_form.about_user.position.data.strip()
				else:
					user.position = ''
	
				user.place = role_form.about_user.place.data
				user.email_new = role_form.about_user.email_new.data
				user.email_modified = role_form.about_user.email_modified.data
				user.email_disapproved = role_form.about_user.email_disapproved.data
				user.email_approved = role_form.about_user.email_approved.data
				user.name = role_form.about_user.full_name.data.strip()
				db.session.commit()
				flash('Данные успешно сохранены.')
			else:
				flash('Пользователь не найден.')
		location_form = AddRemoveLocationForm()
		errors_list = role_form.user_id.errors + role_form.role.errors + role_form.about_user.full_name.errors + role_form.about_user.phone.errors + role_form.about_user.user_data.errors
		for error in errors_list:
			flash(error)
		return render_template('settings.html', ecwid_form = ecwid_form, role_form = role_form, location_form = location_form,\
								users = users, locations=locations, categories=categories, notify1C_form = notify1C_form)
	else:
		user_form = UserSettingsForm()
		if user_form.validate_on_submit():
			if user_form.about_user.phone.data is not None:
				current_user.phone = user_form.about_user.phone.data.strip()
			else:
				current_user.phone = ''
			if user_form.about_user.position.data is not None:
				current_user.position = user_form.about_user.position.data.strip()
			else:
				current_user.position = ''
			current_user.place = user_form.about_user.place.data
			current_user.email_new = user_form.about_user.email_new.data
			current_user.email_modified = user_form.about_user.email_modified.data
			current_user.email_disapproved = user_form.about_user.email_disapproved.data
			current_user.email_approved = user_form.about_user.email_approved.data
			current_user.name = user_form.about_user.full_name.data.strip()
			if current_user.role in [UserRoles.validator,UserRoles.approver] and user_form.about_user.user_data.data is not None:
				current_user.data = ValidateUserData(user_form.about_user.user_data.data)
			db.session.commit()
			flash('Данные успешно сохранены.')
		else:
			errors_list = user_form.about_user.full_name.errors + user_form.about_user.phone.errors + user_form.about_user.user_data.errors
			for error in errors_list:
				flash(error)
		return render_template('settings.html', user_form=user_form, locations=locations, categories=categories)

@bp.route('/remove/<int:user_id>')
@login_required
@role_required([UserRoles.admin])
def RemoveUser(user_id):
	user = User.query.filter(User.id == user_id, or_(User.role == UserRoles.default, User.ecwid_id == current_user.ecwid_id)).first()
	if user is None:
		flash('Пользователь не найден.')
		return redirect(url_for('main.ShowSettings'))
	OrderApproval.query.filter(OrderApproval.user_id == user_id).delete()
	EventLog.query.filter(EventLog.user_id == user_id).delete()
	db.session.delete(user)
	db.session.commit()
	flash('Пользователь успешно удалён.')
	return redirect(url_for('main.ShowSettings'))
	
@bp.route('/location/', methods=['POST'])
@login_required
@role_required([UserRoles.admin])
def AddRemoveLocation():
	form = AddRemoveLocationForm()
	if form.validate_on_submit():
		location_name = form.location_name.data.strip()
		site_name = form.site_name.data.strip()
		location = Location.query.filter(Location.ecwid_id == current_user.ecwid_id, Location.name.ilike(location_name)).first()
		if form.submit1.data is True:
			if location is not None:
				if len(site_name) > 0:
					site = Site.query.filter(Site.loc_id == location.id, Site.name.ilike(site_name)).first()
					if site is None:
						site = Site(name = site_name, loc_id = location.id)
						db.session.add(site)
						db.session.commit()
						flash('Объект {} создан'.format(site_name))
					else:
						flash('Такой объект уже существует')
				else:
					flash('Такой проект уже существует')
			else:	
				location = Location(name = location_name, ecwid_id = current_user.ecwid_id)
				db.session.add(location)
				db.session.commit()		
				flash('Проект {} создан'.format(location_name))
				if len(site_name) > 0:
					site = Site(name = site_name, loc_id = location.id)
					db.session.add(site)
					db.session.commit()
					flash('Объект {} создан'.format(location_name))
		elif form.submit2.data is True:
			if location is not None:
				if len(site_name) == 0:
					Site.query.filter(Site.loc_id == location.id).delete()
					db.session.delete(location)
					db.session.commit()
					flash('Проект {} удален'.format(location_name))
				else:
					site = Site.query.filter(Site.loc_id == location.id, Site.name.ilike(site_name)).first()
					if site is not None:
						db.session.delete(site)
						db.session.commit()
						flash('Объект {} удален'.format(site_name))
					else:
						flash('Такой объект не существует')
					
			else:
				flash('Такого проекта не существует')
	else:
		for error in form.location_name.errors:
			flash(error)
	return redirect(url_for('main.ShowSettings'))
	
@bp.route('/settings1C/', methods=['POST'])
@login_required
@role_required([UserRoles.admin])
def Notify1CSettings():
	form = Notify1CSettingsForm()
	if form.validate_on_submit():
		api_data = ApiData.query.filter_by(ecwid_id = current_user.ecwid_id).first()
		if api_data is None:
			api_data = ApiData(ecwid_id = current_user.ecwid_id)
			db.session.add(api_data)
		api_data.notify_1C = form.enable.data
		api_data.email_1C = form.email.data
		db.session.commit()
		flash('Настройки рассылки 1С успешно сохранены.')
	else:
		for error in form.email.errors + form.enable.errors:
			flash(error)
	return redirect(url_for('main.ShowSettings'))
