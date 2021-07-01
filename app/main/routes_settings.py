from app import db
from flask_login import current_user, login_required
from app.main import bp
from app.models import User, UserRoles, Ecwid, OrderApproval, Category, OrderEvent, Project, Site, AppSettings, Position, Order
from flask import render_template, redirect, url_for, flash
from app.main.forms import EcwidSettingsForm, UserRolesForm, UserSettingsForm, AddRemoveProjectForm, Notify1CSettingsForm
from sqlalchemy import distinct, func, or_
from app.ecwid import EcwidAPIException
from sqlalchemy.exc import SQLAlchemyError
from app.main.utils import role_required, role_forbidden
import json
from json.decoder import JSONDecodeError
from datetime import datetime

'''
################################################################################
Settings page
################################################################################
'''

def RemoveExcessivePosition():
	positions = Position.query.filter(Position.users == None).all()
	for position in positions:
		position.approvals = []
		db.session.delete(position)
	db.session.commit()
		
@bp.route('/settings/', methods=['GET', 'POST'])
@login_required
@role_forbidden([UserRoles.default])
def ShowSettings():

	projects = Project.query.filter(Project.hub_id == current_user.hub_id).order_by(Project.name).all()
	categories = Category.query.filter(Category.hub_id == current_user.hub_id).all()
	if current_user.role == UserRoles.admin:
		user_form = UserRolesForm()
	else:
		user_form = UserSettingsForm()

	if current_user.role in [UserRoles.admin, UserRoles.purchaser, UserRoles.validator]:
		user_form.about_user.categories.choices = [(c.id, c.name) for c in categories]
		user_form.about_user.projects.choices = [(p.id, p.name) for p in projects]

	if user_form.submit.data:
		if user_form.validate_on_submit():
			if current_user.role == UserRoles.admin:
				user = User.query.filter(User.id == user_form.user_id.data).first()
				if user is None:
					flash('Пользователь не найден.')
					return redirect(url_for('main.ShowSettings'))
				user.hub_id = current_user.hub_id
				user.role = user_form.role.data
				user.note = user_form.note.data
			else:
				user = current_user
			
			if user_form.about_user.position.data is not None and user_form.about_user.position.data != '':
				position_name = user_form.about_user.position.data.strip().lower()
				position = Position.query.filter_by(name = position_name, hub_id = user.hub_id).first()
				if position is None:
					position = Position(name = position_name, hub_id = user.hub_id)
				user.position = position
			else:
				user.position = None

			if user.role in [UserRoles.purchaser, UserRoles.validator]:
				if user_form.about_user.categories.data is not None and len(user_form.about_user.categories.data) > 0:
					user.categories = Category.query.filter(Category.id.in_(user_form.about_user.categories.data)).all()
				else:
					user.categories = []	
				if user_form.about_user.projects.data is not None and len(user_form.about_user.projects.data) > 0:
					user.projects = Project.query.filter(Project.id.in_(user_form.about_user.projects.data)).all()
				else:
					user.projects = []
			else:
				user.categories = []
				user.projects = []

			user.phone = user_form.about_user.phone.data
			user.location = user_form.about_user.location.data
			user.email_new = user_form.about_user.email_new.data
			user.email_modified = user_form.about_user.email_modified.data
			user.email_disapproved = user_form.about_user.email_disapproved.data
			user.email_approved = user_form.about_user.email_approved.data
			user.name = user_form.about_user.full_name.data.strip()
			db.session.commit()

			RemoveExcessivePosition()
			
			if user.role in [UserRoles.purchaser, UserRoles.validator]:
				Order.UpdateOrdersPositions(current_user.hub_id)

			flash('Данные успешно сохранены.')
		else:
			errors_list = user_form.about_user.full_name.errors + user_form.about_user.phone.errors + user_form.about_user.categories.errors + user_form.about_user.projects.errors
			for error in errors_list:
				flash(error)
		return redirect(url_for('main.ShowSettings'))


	if current_user.role == UserRoles.admin:
		ecwid_form = EcwidSettingsForm()
		project_form = AddRemoveProjectForm()
		
		app_data = AppSettings.query.filter_by(hub_id = current_user.hub_id).first()
		if app_data is None:
			notify1C_form = Notify1CSettingsForm()
		else:
			notify1C_form = Notify1CSettingsForm(enable = app_data.notify_1C, email = app_data.email_1C)
			
		users = User.query.filter(or_(User.role == UserRoles.default, User.hub_id == current_user.hub_id)).order_by(User.name, User.email).all()
		return render_template('settings.html', ecwid_form = ecwid_form, user_form = user_form, project_form = project_form,\
								users = users, notify1C_form = notify1C_form, projects=projects)
	else:
		return render_template('settings.html', user_form=user_form)

@bp.route('/users/remove/<int:user_id>')
@login_required
@role_required([UserRoles.admin])
def RemoveUser(user_id):
	user = User.query.filter(User.id == user_id, or_(User.role == UserRoles.default, User.hub_id == current_user.hub_id)).first()
	if user is None:
		flash('Пользователь не найден.')
		return redirect(url_for('main.ShowSettings'))
		
	for order in user.orders:
		order.initiative = current_user
		
	db.session.delete(user)
	db.session.commit()
	
	RemoveExcessivePosition()
	
	if user.role in [UserRoles.purchaser, UserRoles.validator]:
		Order.UpdateOrdersPositions(current_user.hub_id)
	
	flash('Пользователь успешно удалён.')
	return redirect(url_for('main.ShowSettings'))
	
@bp.route('/settings/projects/', methods=['POST'])
@login_required
@role_required([UserRoles.admin])
def AddRemoveProject():
	form = AddRemoveProjectForm()
	if form.validate_on_submit():
		project_name = form.project_name.data.strip()
		site_name = form.site_name.data.strip()
		project = Project.query.filter(Project.hub_id == current_user.hub_id, Project.name.ilike(project_name)).first()
		if form.submit1.data is True:
			if project is not None:
				if len(site_name) > 0:
					site = Site.query.filter(Site.project_id == project.id, Site.name.ilike(site_name)).first()
					if site is None:
						site = Site(name = site_name, project_id = project.id)
						db.session.add(site)
						db.session.commit()
						flash('Объект {} создан'.format(site_name))
					else:
						flash('Такой объект уже существует')
				else:
					flash('Такой проект уже существует')
			else:	
				project = Project(name = project_name, hub_id = current_user.hub_id)
				db.session.add(project)
				db.session.commit()		
				flash('Проект {} создан'.format(project_name))
				if len(site_name) > 0:
					site = Site(name = site_name, project_id = project.id)
					db.session.add(site)
					db.session.commit()
					flash('Объект {} создан'.format(project_name))
		elif form.submit2.data is True:
			if project is not None:
				if len(site_name) == 0:
					Site.query.filter(Site.project_id == project.id).delete()
					db.session.delete(project)
					db.session.commit()
					flash('Проект {} удален'.format(project_name))
				else:
					site = Site.query.filter(Site.project_id == project.id, Site.name.ilike(site_name)).first()
					if site is not None:
						db.session.delete(site)
						db.session.commit()
						flash('Объект {} удален'.format(site_name))
					else:
						flash('Такой объект не существует')
			else:
				flash('Такого проекта не существует')
	else:
		for error in form.project_name.errors:
			flash(error)
	return redirect(url_for('main.ShowSettings'))
	
@bp.route('/settings/1C/', methods=['POST'])
@login_required
@role_required([UserRoles.admin])
def Notify1CSettings():
	form = Notify1CSettingsForm()
	if form.validate_on_submit():
		app_data = AppSettings.query.filter_by(hub_id = current_user.hub_id).first()
		if app_data is None:
			app_data = AppSettings(hub_id = current_user.hub_id)
			db.session.add(app_data)
		app_data.notify_1C = form.enable.data
		app_data.email_1C = form.email.data
		db.session.commit()
		flash('Настройки рассылки 1С успешно сохранены.')
	else:
		for error in form.email.errors + form.enable.errors:
			flash(error)
	return redirect(url_for('main.ShowSettings'))

	
@bp.route('/settings/ecwid/', methods=['POST'])
@login_required
@role_required([UserRoles.admin])
def ConfigureEcwid():
	ecwid_form = EcwidSettingsForm()
	if ecwid_form.validate_on_submit():
		if current_user.hub is None:
			current_user.hub = Ecwid()
		current_user.hub.partners_key = ecwid_form.partners_key.data
		current_user.hub.client_id = ecwid_form.client_id.data
		current_user.hub.client_secret = ecwid_form.client_secret.data
		current_user.hub.id = ecwid_form.store_id.data
		try:
			current_user.hub.GetStoreToken()
			profile = current_user.hub.GetStoreProfile()
			db.session.commit()
			flash('Данные успешно сохранены.')
		except (SQLAlchemyError, EcwidAPIException):
			db.session.rollback()
			flash('Ошибка API или магазин уже используется.')
			flash('Возможно неверные настройки?')
		return redirect(url_for('main.ShowSettings'))
	else:
		errors_list = role_form.user_id.errors + role_form.role.errors + role_form.about_user.full_name.errors + role_form.about_user.phone.errors + role_form.about_user.categories.errors + role_form.about_user.projects.errors
		for error in errors_list:
			flash(error)
	return redirect(url_for('main.ShowSettings'))
