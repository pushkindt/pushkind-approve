from app import db
from flask_login import current_user, login_required
from app.main import bp
from app.models import User, UserRoles, Ecwid, OrderComment, OrderApproval, CacheCategories
from flask import render_template, redirect, url_for, flash
from app.main.forms import EcwidSettingsForm, UserRolesForm, UserSettingsForm
from sqlalchemy import distinct, func, or_
from app.ecwid import EcwidAPIException
from sqlalchemy.exc import SQLAlchemyError
from app.main.utils import role_required, role_forbidden

'''
################################################################################
Settings page
################################################################################
'''

@bp.route('/settings/', methods=['GET', 'POST'])
@login_required
@role_forbidden([UserRoles.default])
def ShowSettings():
	locations = [loc[0] for loc in db.session.query(distinct(func.lower(User.location))).filter(User.ecwid_id == current_user.ecwid_id, User.role == UserRoles.initiative).all()]
	categories = CacheCategories.query.all()
	if current_user.role == UserRoles.admin:
		if not current_user.hub:
			current_user.hub = Ecwid()
			db.session.commit()
		ecwid_form = EcwidSettingsForm()
		role_form = UserRolesForm()
		users = User.query.filter(or_(User.role == UserRoles.default, User.ecwid_id == current_user.ecwid_id)).all()
		role_form.user_id.choices = [(u.id, u.email) for u in users if u.id != current_user.id]
		if ecwid_form.submit1.data and ecwid_form.validate_on_submit():
			current_user.hub.partners_key = ecwid_form.partners_key.data
			current_user.hub.client_id = ecwid_form.client_id.data
			current_user.hub.client_secret = ecwid_form.client_secret.data
			current_user.hub.store_id = ecwid_form.store_id.data
			try:
				current_user.hub.EcwidGetStoreToken()
				db.session.commit()
				flash('Данные успешно сохранены.')
			except (SQLAlchemyError, EcwidAPIException):
				db.session.rollback()
				flash('Ошибка API или магазин уже используется.')
				flash('Возможно неверные настройки?')
		elif role_form.submit2.data and role_form.validate_on_submit():
			user = User.query.filter(User.id == role_form.user_id.data).first()
			if user:
				user.ecwid_id = current_user.ecwid_id
				user.role = UserRoles(role_form.role.data)
				if role_form.about_user.phone.data:
					user.phone = role_form.about_user.phone.data.strip()
				else:
					user.phone = ''
				if role_form.about_user.position.data:
					user.position = role_form.about_user.position.data.strip()
				else:
					user.position = ''
				user.name = role_form.about_user.full_name.data.strip()
				if role_form.about_user.location.data:
					user.location = role_form.about_user.location.data.strip()
				db.session.commit()
				flash('Данные успешно сохранены.')
			else:
				flash('Пользователь не найден.')
		return render_template('settings.html', ecwid_form = ecwid_form, role_form = role_form, users = users)
	else:
		user_form = UserSettingsForm()
		if user_form.validate_on_submit():
			if user_form.about_user.phone.data:
				current_user.phone = user_form.about_user.phone.data.strip()
			else:
				current_user.phone = ''
			if user_form.about_user.position.data:
				current_user.position = user_form.about_user.position.data.strip()
			else:
				current_user.position = ''
			current_user.name = user_form.about_user.full_name.data.strip()
			if user_form.about_user.location.data:
				current_user.location = user_form.about_user.location.data.strip()
			db.session.commit()
			flash('Данные успешно сохранены.')
		return render_template('settings.html', user_form=user_form, locations=locations, categories=categories)

@bp.route('/remove/<int:user_id>')
@login_required
@role_required([UserRoles.admin])
def RemoveUser(user_id):
	user = User.query.filter(User.id == user_id, or_(User.role == UserRoles.default, User.ecwid_id == current_user.ecwid_id)).first()
	if not user:
		flash('Пользователь не найден.')
		return redirect(url_for('main.ShowSettings'))
	OrderApproval.query.filter(OrderApproval.user_id == user_id).delete()
	OrderComment.query.filter(OrderComment.user_id == user_id).delete()
	db.session.delete(user)
	db.session.commit()
	flash('Пользователь успешно удалён.')
	return redirect(url_for('main.ShowSettings'))