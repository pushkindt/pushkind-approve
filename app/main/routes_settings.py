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

    projects = Project.query.filter(
        Project.hub_id == current_user.hub_id).order_by(Project.name).all()
    categories = Category.query.filter(
        Category.hub_id == current_user.hub_id).all()
    if current_user.role == UserRoles.admin:
        user_form = UserRolesForm()
    else:
        user_form = UserSettingsForm()

    if current_user.role in [UserRoles.admin, UserRoles.purchaser, UserRoles.validator]:
        user_form.about_user.categories.choices = [
            (c.id, c.name) for c in categories]
        user_form.about_user.projects.choices = [
            (p.id, p.name) for p in projects]

    if user_form.submit.data:
        if user_form.validate_on_submit():
            if current_user.role == UserRoles.admin:
                user = User.query.filter(
                    User.id == user_form.user_id.data).first()
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
                position = Position.query.filter_by(
                    name=position_name, hub_id=user.hub_id).first()
                if position is None:
                    position = Position(name=position_name, hub_id=user.hub_id)
                user.position = position
            else:
                user.position = None

            if user.role in [UserRoles.purchaser, UserRoles.validator]:
                if user_form.about_user.categories.data is not None and len(user_form.about_user.categories.data) > 0:
                    user.categories = Category.query.filter(
                        Category.id.in_(user_form.about_user.categories.data)).all()
                else:
                    user.categories = []
                if user_form.about_user.projects.data is not None and len(user_form.about_user.projects.data) > 0:
                    user.projects = Project.query.filter(
                        Project.id.in_(user_form.about_user.projects.data)).all()
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
            errors_list = user_form.about_user.full_name.errors + user_form.about_user.phone.errors + \
                user_form.about_user.categories.errors + user_form.about_user.projects.errors
            for error in errors_list:
                flash(error)
        return redirect(url_for('main.ShowSettings'))

    if current_user.role == UserRoles.admin:
        users = User.query.filter(or_(User.role == UserRoles.default, User.hub_id ==
                                  current_user.hub_id)).order_by(User.name, User.email).all()
        return render_template('settings.html', user_form=user_form, users=users)
    else:
        return render_template('settings.html', user_form=user_form)


@bp.route('/users/remove/<int:user_id>')
@login_required
@role_required([UserRoles.admin])
def RemoveUser(user_id):
    user = User.query.filter(User.id == user_id, or_(
        User.role == UserRoles.default, User.hub_id == current_user.hub_id)).first()
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
