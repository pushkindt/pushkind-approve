from sqlalchemy.sql.functions import current_user
from app import db
from flask_login import login_required, current_user
from app.main import bp
from app.models import UserRoles, OrderLimit, Project, Site, OrderLimitsIntervals
from flask import render_template, flash, redirect, url_for, request
from app.main.utils import ecwid_required, role_forbidden
from app.main.forms import AddLimitForm


@bp.route('/limits/', methods=['GET'])
@bp.route('/limits/show', methods=['GET'])
@login_required
@role_forbidden([UserRoles.default])
@ecwid_required
def ShowLimits():
    filter_from = request.args.get('from', default=None, type=int)
    try:
        filter_from = OrderLimitsIntervals(filter_from)
    except ValueError:
        filter_from = None

    OrderLimit.update_current(current_user.hub_id)
    projects = Project.query
    if current_user.role != UserRoles.admin:
        projects = projects.filter_by(enabled=True)
    projects = projects.filter_by(hub_id=current_user.hub_id)
    projects = projects.order_by(Project.name).all()

    form = AddLimitForm()
    form.project.choices = [(p.id, p.name) for p in projects]
    form.project.default = 0
    form.site.choices = [(0, 'Выберите объект...')]
    form.site.default = 0
    form.process()

    limits = OrderLimit.query.filter_by(hub_id=current_user.hub_id)
    if filter_from is not None:
        limits = limits.filter_by(interval=filter_from)
    limits = limits.all()

    return render_template(
        'limits.html',
        limits=limits,
        projects=projects,
        intervals=OrderLimitsIntervals,
        filter_from=filter_from,
        form=form
    )


@bp.route('/limits/add', methods=['POST'])
@login_required
@role_forbidden([UserRoles.default])
@ecwid_required
def AddLimit():
    projects = Project.query
    if current_user.role != UserRoles.admin:
        projects = projects.filter_by(enabled=True)
    projects = projects.filter_by(hub_id=current_user.hub_id)
    projects = projects.all()
    form = AddLimitForm()
    form.project.choices = [(p.id, p.name) for p in projects]

    project = Project.query.filter_by(
        id=form.project.data,
        hub_id=current_user.hub_id
    ).first()

    if project is not None:
        form.site.choices = [(s.id, s.name) for s in project.sites]
    else:
        form.site.choices = []

    if form.validate_on_submit():
        limit = OrderLimit(
            hub_id = current_user.hub_id,
            value = form.value.data,
            interval = form.interval.data
        )
        if form.site.data is not None:
            site = (
                Site.query.filter_by(id=form.site.data)
                .join(Project).filter_by(hub_id=current_user.hub_id).first()
            )
            if site is None:
                flash('Объект не найден')
                return redirect(url_for('main.ShowLimits'))
            limit.site_id = site.id
            limit.project_id = site.project_id
        else:
            limit.project_id = form.project.data
        db.session.add(limit)
        db.session.commit()
        flash('Лимит успешно добавлен.')
    else:
        for error in form.interval.errors + form.value.errors + form.project.errors + form.site.errors:
            flash(error)
    return redirect(url_for('main.ShowLimits'))

@bp.route('/limits/remove/<int:id>', methods=['GET'])
@login_required
@role_forbidden([UserRoles.default])
@ecwid_required
def RemoveLimit(id):
    limit = OrderLimit.query.filter_by(hub_id=current_user.hub_id, id=id).first()
    if limit is not None:
        db.session.delete(limit)
        db.session.commit()
        flash('Лимит успешно удалён.')
    else:
        flash('Лимит не найден.')
    return redirect(url_for('main.ShowLimits'))