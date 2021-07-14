from app import db
from flask_login import current_user, login_required
from app.main import bp
from app.models import User, UserRoles, Ecwid, OrderApproval, Category, OrderEvent, Project, Site
from app.models import AppSettings, Position, Order
from flask import render_template, redirect, url_for, flash
from app.main.forms import EcwidSettingsForm, AddRemoveProjectForm
from app.main.forms import Notify1CSettingsForm, CategoryResponsibilityForm
from sqlalchemy import distinct, func, or_
from app.ecwid import EcwidAPIException
from sqlalchemy.exc import SQLAlchemyError
from app.main.utils import role_required, role_forbidden
import json
from json.decoder import JSONDecodeError
from datetime import datetime


@bp.route('/admin/', methods=['GET', 'POST'])
@login_required
@role_forbidden([UserRoles.default])
def ShowAdminPage():
    ecwid_form = EcwidSettingsForm()
    project_form = AddRemoveProjectForm()
    category_form = CategoryResponsibilityForm()

    app_data = AppSettings.query.filter_by(hub_id=current_user.hub_id).first()
    if app_data is None:
        notify1C_form = Notify1CSettingsForm()
    else:
        notify1C_form = Notify1CSettingsForm(
            enable=app_data.notify_1C, email=app_data.email_1C)

    projects = Project.query.filter(
        Project.hub_id == current_user.hub_id).order_by(Project.name).all()
    categories = Category.query.filter(
        Category.hub_id == current_user.hub_id).all()

    return render_template('admin.html',
                           ecwid_form=ecwid_form,
                           project_form=project_form,
                           category_form=category_form,
                           notify1C_form=notify1C_form,
                           projects=projects, categories=categories)


@bp.route('/admin/projects/', methods=['POST'])
@login_required
@role_required([UserRoles.admin])
def AddRemoveProject():
    form = AddRemoveProjectForm()
    if form.validate_on_submit():
        project_name = form.project_name.data.strip()
        site_name = form.site_name.data.strip()
        project = Project.query.filter(
            Project.hub_id == current_user.hub_id, Project.name.ilike(project_name)).first()
        if form.submit1.data is True:
            if project is not None:
                if len(site_name) > 0:
                    site = Site.query.filter(
                        Site.project_id == project.id, Site.name.ilike(site_name)).first()
                    if site is None:
                        site = Site(name=site_name, project_id=project.id)
                        db.session.add(site)
                        db.session.commit()
                        flash('Объект {} создан'.format(site_name))
                    else:
                        flash('Такой объект уже существует')
                else:
                    flash('Такой проект уже существует')
            else:
                project = Project(name=project_name,
                                  hub_id=current_user.hub_id)
                db.session.add(project)
                db.session.commit()
                flash('Проект {} создан'.format(project_name))
                if len(site_name) > 0:
                    site = Site(name=site_name, project_id=project.id)
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
                    site = Site.query.filter(
                        Site.project_id == project.id, Site.name.ilike(site_name)).first()
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
    return redirect(url_for('main.ShowAdminPage'))


@bp.route('/admin/1C/', methods=['POST'])
@login_required
@role_required([UserRoles.admin])
def Notify1CSettings():
    form = Notify1CSettingsForm()
    if form.validate_on_submit():
        app_data = AppSettings.query.filter_by(
            hub_id=current_user.hub_id).first()
        if app_data is None:
            app_data = AppSettings(hub_id=current_user.hub_id)
            db.session.add(app_data)
        app_data.notify_1C = form.enable.data
        app_data.email_1C = form.email.data
        db.session.commit()
        flash('Настройки рассылки 1С успешно сохранены.')
    else:
        for error in form.email.errors + form.enable.errors:
            flash(error)
    return redirect(url_for('main.ShowAdminPage'))


@bp.route('/admin/ecwid/', methods=['POST'])
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
        return redirect(url_for('main.ShowAdminPage'))
    else:
        errors_list = role_form.user_id.errors + role_form.role.errors + role_form.about_user.full_name.errors + \
            role_form.about_user.phone.errors + role_form.about_user.categories.errors + \
            role_form.about_user.projects.errors
        for error in errors_list:
            flash(error)
    return redirect(url_for('main.ShowAdminPage'))


@bp.route('/admin/categories/', methods=['POST'])
@login_required
@role_required([UserRoles.admin])
def SaveCategoryResponsibility():
    form = CategoryResponsibilityForm()
    if form.validate_on_submit():
        category = Category.query.filter_by(
            id=form.category_id.data, hub_id=current_user.hub_id).first()
        if category is None:
            flash("Категория с таким идентификатором не найдена.")
        else:
            category.responsible = form.responsible.data.strip()
            category.functional_budget = form.functional_budget.data.strip()
            db.session.commit()
            flash('Ответственный и ФДБ для категории сохранёны.')
    return redirect(url_for('main.ShowAdminPage'))
