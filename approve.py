from app import cli, create_app, db
from app.models import (
    AppSettings,
    CashflowStatement,
    Category,
    EventType,
    IncomeStatement,
    Order,
    OrderApproval,
    OrderCategory,
    OrderEvent,
    OrderLimit,
    OrderPosition,
    OrderStatus,
    Position,
    Project,
    Site,
    User,
    UserCategory,
    UserProject,
    UserRoles,
    Vendor,
)

application = create_app()
cli.register(application)


@application.shell_context_processor
def make_shell_context():
    return {
        "db": db,
        "User": User,
        "UserRoles": UserRoles,
        "Vendor": Vendor,
        "OrderApproval": OrderApproval,
        "OrderStatus": OrderStatus,
        "Category": Category,
        "AppSettings": AppSettings,
        "OrderEvent": OrderEvent,
        "Project": Project,
        "Site": Site,
        "Position": Position,
        "Order": Order,
        "UserCategory": UserCategory,
        "UserProject": UserProject,
        "OrderPosition": OrderPosition,
        "OrderCategory": OrderCategory,
        "EventType": EventType,
        "IncomeStatement": IncomeStatement,
        "CashflowStatement": CashflowStatement,
        "OrderLimit": OrderLimit,
    }
