import os
import re
import tempfile

import pytest

from app import create_app, db


class TestConfig:
    APPLICATION_TITLE = "test"
    ADMIN_EMAIL = "email@email.email"
    SECRET_KEY = "you-will-never-guess"
    SQLALCHEMY_DATABASE_URI = ""
    ECWID_JS_URL = ""
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = None
    MAIL_PORT = 25
    MAIL_USE_SSL = False
    MAIL_USE_TLS = False
    MAIL_USERNAME = ""
    MAIL_PASSWORD = ""
    MAIL_SENDERNAME = ""
    MOMENT_DEFAULT_FORMAT = "DD.MM.YYYY HH:mm"
    PASSWORD = "password"
    WTF_CSRF_ENABLED = True


def signup(client, email, password):
    response = client.get("/auth/signup/", follow_redirects=True)
    match = re.search(
        r'<input name="csrf_token" type="hidden" value="(.*)">',
        response.text,
    )
    assert match
    return client.post(
        "/auth/signup/",
        data=dict(
            email=email,
            password=password,
            password2=password,
            csrf_token=match.group(1),
        ),
        follow_redirects=True,
    )


def login(client, email, password):
    response = client.get("/auth/login/", follow_redirects=True)
    match = re.search(
        r'<input name="csrf_token" type="hidden" value="(.*)">',
        response.text,
    )
    assert match
    return client.post(
        "/auth/login/",
        data=dict(email=email, password=password, csrf_token=match.group(1)),
        follow_redirects=True,
    )


def logout(client):
    return client.get("/auth/logout", follow_redirects=True)


@pytest.fixture
def client():
    db_fd, db_path = tempfile.mkstemp()
    TestConfig.SQLALCHEMY_DATABASE_URI = "sqlite:///" + db_path
    app = create_app(TestConfig)
    app_context = app.app_context()
    app_context.push()
    db.create_all()
    with app.test_client() as client:
        yield client
    os.close(db_fd)
    os.unlink(db_path)


def test_empty_db(client):
    """Start with a blank database."""
    rv = client.get("/")
    assert b"Redirecting..." in rv.data


def test_auth_module(client):
    """Make sure login and logout works."""

    email = TestConfig.ADMIN_EMAIL
    password = TestConfig.PASSWORD

    rv = login(client, email, password)
    assert "Некорректный логин или пароль." in rv.data.decode("utf-8")

    rv = signup(client, email, password)
    assert "Теперь пользователь может войти." in rv.data.decode("utf-8")

    rv = login(client, email, password)
    assert "403 FORBIDDEN" == rv.status

    rv = logout(client)
    assert "Авторизация" in rv.data.decode("utf-8")
