import click

from app import db
from app.models import Vendor, User, UserRoles

def register(app):
    @app.cli.group()
    def bootstrap():
        pass

    @bootstrap.command()
    @click.argument('hub_name')
    @click.argument('hub_email')
    @click.argument('hub_password')
    def init(hub_name, hub_email, hub_password):
        admin = User(
            email=hub_email,
            role=UserRoles.admin,
            name=hub_name
        )
        admin.set_password(hub_password)
        db.session.add(admin)
        db.session.commit()
        hub = Vendor(
            admin_id=admin.id,
            email=hub_email,
            name=hub_name
        )
        db.session.add(hub)
        db.session.commit()
        admin.hub=hub
        db.session.commit()