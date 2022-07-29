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
        .get('DATABASE_URL', 'sqlite:///' + os.path.join(basedir, 'app.db'))
    )
    PLACEHOLDER_IMAGE = '/static/placeholder.png'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL') is not None
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_SENDERNAME=os.environ.get('MAIL_SENDERNAME') or 'Sender'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MOMENT_DEFAULT_FORMAT = (
        os.environ.get('MOMENT_DEFAULT_FORMAT') or 'DD.MM.YYYY HH:mm'
    )
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB limit for uploading
    MAX_ZIP_FILE_SIZE = 1 * 1024 * 1024  # 1MB limit for a file in a zip archive
