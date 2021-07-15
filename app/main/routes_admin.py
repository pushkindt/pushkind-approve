from app import db
from flask_login import current_user, login_required
from app.main import bp
from app.models import UserRoles, Ecwid, Category, Project, Site
from app.models import AppSettings
from flask import render_template, redirect, url_for, flash
from app.main.forms import EcwidSettingsForm, AddProjectForm, AddSiteForm, EditProjectForm, EditSiteForm
from app.main.forms import Notify1CSettingsForm, CategoryResponsibilityForm
from app.ecwid import EcwidAPIException
from sqlalchemy.exc import SQLAlchemyError
from app.main.utils import role_required, role_forbidden


@bp.route('/admin/', methods=['GET', 'POST'])
@login_required
@role_forbidden([UserRoles.default])
def ShowAdminPage():

    forms = {
        'ecwid': EcwidSettingsForm(),
        'category': CategoryResponsibilityForm(),
        'add_project': AddProjectForm(),
        'edit_project': EditProjectForm(),
        'add_site': AddSiteForm(),
        'edit_site': EditSiteForm()
    }

    app_data = AppSettings.query.filter_by(hub_id=current_user.hub_id).first()
    if app_data is None:
        forms['notify1C'] = Notify1CSettingsForm()
    else:
        forms['notify1C'] = Notify1CSettingsForm(
            enable=app_data.notify_1C, email=app_data.email_1C)

    projects = Project.query.filter(
        Project.hub_id == current_user.hub_id).order_by(Project.name).all()
    categories = Category.query.filter(
        Category.hub_id == current_user.hub_id).all()

    return render_template('admin.html',
                           forms=forms,
                           projects=projects, categories=categories)


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


@bp.route('/admin/project/add', methods=['POST'])
@login_required
@role_required([UserRoles.admin])
def AddProject():
    form = AddProjectForm()
    if form.validate_on_submit():
        project_name = form.project_name.data.strip()
        uid = form.uid.data.strip() if form.uid.data is not None else None
        project = Project.query.filter_by(name=project_name).first()
        if project is None:
            project = Project(name=project_name, uid=uid,
                              hub_id=current_user.hub_id)
            db.session.add(project)
            db.session.commit()
            flash(f'Проект {project_name} добавлен.')
        else:
            flash(f'Проект {project_name} уже существует.')
    else:
        for error in form.project_name.errors + form.uid.errors:
            flash(error)
    return redirect(url_for('main.ShowAdminPage'))


@bp.route('/admin/site/add', methods=['POST'])
@login_required
@role_required([UserRoles.admin])
def AddSite():
    form = AddSiteForm()
    if form.validate_on_submit():
        site_name = form.site_name.data.strip()
        uid = form.uid.data.strip() if form.uid.data is not None else None
        site = Site.query.filter_by(name=site_name).first()
        if site is None:
            site = Site(name=site_name, uid=uid,
                        project_id=form.project_id.data)
            db.session.add(site)
            db.session.commit()
            flash(f'Объект {site_name} добавлен.')
        else:
            flash(f'Объект {site_name} уже существует.')
    else:
        for error in form.site_name.errors + form.uid.errors + form.project_id.errors:
            flash(error)
    return redirect(url_for('main.ShowAdminPage'))


@bp.route('/admin/project/remove/<int:id>')
@login_required
@role_required([UserRoles.admin])
def RemoveProject(id):
    project = Project.query.filter_by(id=id).first()
    if project is not None:
        db.session.delete(project)
        db.session.commit()
        flash(f'Проект {project.name} удален.')
    else:
        flash('Такого проекта не существует.')
    return redirect(url_for('main.ShowAdminPage'))


@bp.route('/admin/project/edit/', methods=['POST'])
@login_required
@role_required([UserRoles.admin])
def EditProject():
    form = EditProjectForm()
    if form.validate_on_submit():
        project = Project.query.filter_by(id=form.project_id.data).first()
        if project is not None:
            project_name = form.project_name.data.strip()
            existed = Project.query.filter_by(name=project_name).first()
            if existed is None or existed.id == project.id:
                project.name = project_name
                project.uid = form.uid.data.strip() if form.uid.data is not None else None
                db.session.commit()
                flash(f'Проект {project_name} изменён.')
            else:
                flash(f'Проект {project_name} уже существует.')
        else:
            flash('Такого проекта не существует.')
    else:
        for error in form.project_id.errors + form.project_name.errors + form.uid.errors:
            flash(error)
    return redirect(url_for('main.ShowAdminPage'))


@bp.route('/admin/site/remove/<int:id>')
@login_required
@role_required([UserRoles.admin])
def RemoveSite(id):
    site = Site.query.filter_by(id=id).first()
    if site is not None:
        db.session.delete(site)
        db.session.commit()
        flash(f'Объект {site.name} удален.')
    else:
        flash('Такой объект не существует.')
    return redirect(url_for('main.ShowAdminPage'))


@bp.route('/admin/site/edit/', methods=['POST'])
@login_required
@role_required([UserRoles.admin])
def EditSite():
    form = EditSiteForm()
    if form.validate_on_submit():
        site = Site.query.filter_by(id=form.site_id.data).first()
        if site is not None:
            site_name = form.site_name.data.strip()
            existed = Site.query.filter_by(name=site_name).first()
            if existed is None or existed.id == site.id:
                site.name = site_name
                site.uid = form.uid.data.strip() if form.uid.data is not None else None
                db.session.commit()
                flash(f'Объект {site_name} изменён.')
            else:
                flash(f'Объект {site_name} уже существует.')
        else:
            flash('Такой объект не существует.')
    else:
        for error in form.site_id.errors + form.site_name.errors + form.uid.errors:
            flash(error)
    return redirect(url_for('main.ShowAdminPage'))
