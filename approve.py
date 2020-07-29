from app import create_app, db
from app.models import User, UserRoles, Ecwid, OrderApproval

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'UserRoles':UserRoles, 'Ecwid':Ecwid, 'OrderApproval':OrderApproval}