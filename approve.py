from app import create_app, db
from app.models import User, UserRoles, Ecwid, OrderApproval, OrderStatus
from app.models import UserCategory, UserProject, OrderPosition, OrderCategory
from app.models import EventType, IncomeStatement, CashflowStatement
from app.models import Category, AppSettings, OrderEvent, Project, Site, Order
from app.models import Position, OrderLimit


application = create_app()

@application.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'UserRoles': UserRoles,
        'Ecwid': Ecwid,
        'OrderApproval': OrderApproval,
        'OrderStatus': OrderStatus,
        'Category': Category,
        'AppSettings': AppSettings,
        'OrderEvent': OrderEvent,
        'Project': Project,
        'Site': Site,
        'Position': Position,
        'Order': Order,
        'UserCategory': UserCategory,
        'UserProject': UserProject,
        'OrderPosition': OrderPosition,
        'OrderCategory': OrderCategory,
        'EventType': EventType,
        'IncomeStatement': IncomeStatement,
        'CashflowStatement': CashflowStatement,
        'OrderLimit': OrderLimit
    }
