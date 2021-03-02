from app import create_app, db
from app.models import User, UserRoles, Ecwid, OrderApproval, OrderStatus, CacheCategories, ApiData, EventLog, Location, Site

application = create_app()

@application.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'UserRoles':UserRoles, 'Ecwid':Ecwid, 'OrderApproval':OrderApproval,\
	'OrderStatus':OrderStatus, 'CacheCategories':CacheCategories, 'ApiData':ApiData, 'EventLog':EventLog,\
	'Location':Location, 'Site':Site}