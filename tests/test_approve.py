import os
import tempfile
from sqlalchemy.sql import text

import pytest

from app import create_app, db

class TestConfig:
    APPLICATION_TITLE = 'test'
    ADMIN_EMAIL = 'email@email.email'
    SECRET_KEY = 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = ''
    ECWID_JS_URL = ''
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = ''
    MAIL_PORT = 25
    MAIL_USE_SSL = False
    MAIL_USE_TLS = False
    MAIL_USERNAME = ''
    MAIL_PASSWORD = ''
    MOMENT_DEFAULT_FORMAT = 'DD.MM.YYYY HH:mm'
    PASSWORD = 'password'
    WTF_CSRF_ENABLED = False


def signup(client, email, password):
    return client.post(
        '/auth/signup',
        data=dict(
            email=email,
            password=password,
            password2=password
        ),
        follow_redirects=True
    )

def login(client, email, password):
    return client.post(
        '/auth/login',
        data=dict(
            email=email,
            password=password
        ),
        follow_redirects=True
    )

def logout(client):
    return client.get('/auth/logout', follow_redirects=True)

@pytest.fixture
def client():
    db_fd, db_path = tempfile.mkstemp()
    TestConfig.SQLALCHEMY_DATABASE_URI = 'sqlite:///' + db_path
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
    rv = client.get('/')
    assert b'Redirecting...' in rv.data

def test_auth_module(client):
    """Make sure login and logout works."""

    email = TestConfig.ADMIN_EMAIL
    password = TestConfig.PASSWORD

    rv = login(client, email, password)
    assert 'Некорректный логин или пароль.' in rv.data.decode('utf-8')

    rv = signup(client, email, password)
    assert 'Теперь пользователь может войти.' in rv.data.decode('utf-8')

    rv = login(client, email, password)
    assert '403 FORBIDDEN' == rv.status

    rv = logout(client)
    assert 'Авторизация' in rv.data.decode('utf-8')