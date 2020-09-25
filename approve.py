from app import create_app, db
from app.models import User, UserRoles, Ecwid, OrderApproval, OrderComment, OrderStatus, CacheCategories, ApiData

application = create_app()

@application.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'UserRoles':UserRoles, 'Ecwid':Ecwid, 'OrderApproval':OrderApproval, 'OrderComment':OrderComment, 'OrderStatus':OrderStatus, 'CacheCategories':CacheCategories, 'ApiData':ApiData}