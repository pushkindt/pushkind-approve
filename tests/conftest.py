from datetime import datetime

import pytest
from pytz import timezone

from approve import create_app
from approve.extensions import db
from approve.models import User, Vendor, Category, Product, UserRoles, Project


@pytest.fixture(scope="session")
def hub():
    vendor = Vendor(id=1, name="Novolex", email="novolex@example.com")
    return vendor

@pytest.fixture(scope="session")
def users(hub):
    usrs = []
    for role in UserRoles:
        user = User(id=role.value, name=role.name, email=f"{role.name}@example.com", role=role)
        user.set_password("123456")
        user.hub = hub
        usrs.append(user)
    return usrs


@pytest.fixture(scope="session")
def app(hub, users):
    app = create_app(FORCE_ENV_FOR_DYNACONF="testing")
    with app.app_context():
        db.create_all()
        db.session.add(hub)
        for user in users:
            db.session.add(user)
        db.session.commit()
        yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    test_client = app.test_client()
    with test_client.session_transaction() as session:
        session["user_id"] = 1
    return test_client


@pytest.fixture()
def mock_datetime():
    return datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone("UTC"))
