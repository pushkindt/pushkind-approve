import os
import tempfile

import pytest

from app import create_app

class TestConfig:
    APPLICATION_TITLE = 'test'
    ADMIN_EMAIL = 'email@email.email'
    SECRET_KEY = 'you-will-never-guess'
    ICU_EXTENSION_PATH = 'libsqliteicu.so'
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

@pytest.fixture
def client():
    db_fd, db_path = tempfile.mkstemp()
    TestConfig.SQLALCHEMY_DATABASE_URI = 'sqlite:///' + db_path
    app = create_app(TestConfig)
    with app.test_client() as client:
        yield client
    os.close(db_fd)
    os.unlink(db_path)