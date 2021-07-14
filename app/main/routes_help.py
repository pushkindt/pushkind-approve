from app import db
from flask_login import current_user, login_required
from app.main import bp
from app.models import UserRoles, Project, Category, User, UserProject, UserCategory
from flask import render_template, flash, request, redirect, url_for
from app.main.utils import ecwid_required, role_forbidden, role_required

'''
################################################################################
Responibility page
################################################################################
'''


@bp.route('/help/', methods=['GET', 'POST'])
@login_required
@role_forbidden([UserRoles.default])
@ecwid_required
def ShowHelp():
    project_responsibility = dict()
    projects = Project.query.filter_by(hub_id=current_user.hub_id).join(UserProject).join(
        User).filter_by(role=UserRoles.validator).order_by(Project.name).all()

    for project in projects:
        project_responsibility[project.name] = {
            'users': project.users, 'positions': set()}
        for user in project.users:
            position = user.position.name if user.position else 'не указана'
            project_responsibility[project.name]['positions'].add(position)

    category_responsibility = dict()
    categories = Category.query.filter_by(hub_id=current_user.hub_id).join(UserCategory).join(
        User).filter_by(role=UserRoles.validator).order_by(Category.name).all()

    for category in categories:
        category_responsibility[category.name] = {
            'users': category.users, 'positions': set()}
        for user in category.users:
            position = user.position.name if user.position else 'не указана'
            category_responsibility[category.name]['positions'].add(position)

    return render_template('help.html', projects=project_responsibility, categories=category_responsibility)
