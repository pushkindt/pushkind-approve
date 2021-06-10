from app import db
from flask_login import current_user, login_required
from app.main import bp
from app.models import UserRoles, Position, User
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
	positions = Position.query.filter_by(hub_id = current_user.hub_id).join(User).filter_by(role = UserRoles.validator).all()

	responsibilities = dict()
	
	for position in positions:
		responsibilities[position.name] = {'categories':set(), 'projects':set(), 'users':position.users}
		for user in position.users:
			for category in user.categories:
				responsibilities[position.name]['categories'].add(category.name)
			for project in user.projects:
				responsibilities[position.name]['projects'].add(project.name)
	return render_template('help.html', responsibilities = responsibilities)

