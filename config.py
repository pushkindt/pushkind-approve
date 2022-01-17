import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    APPLICATION_TITLE = (
        os.environ.get('APPLICATION_TITLE') or 'Application Title'
    )
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') or 'admin@example.com'
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    ICU_EXTENSION_PATH = os.path.join(basedir, 'libsqliteicu.so')
    SQLALCHEMY_DATABASE_URI = (
        os.environ
        .get('DATABASE_URL', 'file:' + os.path.join(basedir, 'app.db'))
        .replace('file:', 'sqlite:///', 1)
    )
    ECWID_JS_URL = os.environ.get('ECWID_JS_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL') is not None
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MOMENT_DEFAULT_FORMAT = (
        os.environ.get('MOMENT_DEFAULT_FORMAT') or 'DD.MM.YYYY HH:mm'
    )
