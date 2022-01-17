import logging
from logging.handlers import RotatingFileHandler
import os

from flask import Flask, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from sqlalchemy.event import listen
from flask_mail import Mail
from flask_moment import Moment

from config import Config


DB_COLLATE = 'ru_RU.UTF-8'

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.PerformLogin'
login.login_message = 'Пожалуйста, авторизуйтесь, чтобы увидеть эту страницу.'
mail = Mail()
moment = Moment()

def load_extension(dbapi_conn, unused):
    dbapi_conn.enable_load_extension(True)
    dbapi_conn.load_extension(current_app.config['ICU_EXTENSION_PATH'])
    dbapi_conn.enable_load_extension(False)
    dbapi_conn.execute(
        "SELECT icu_load_collation(?, 'ICU_EXT_1')",
        (DB_COLLATE,)
    )

# pylint: disable=C0413,C0415
def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    moment.init_app(app)

    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    if app.debug is False:
        if os.path.exists('logs') is False:
            os.mkdir('logs')
        file_handler = RotatingFileHandler(
            f'logs/{__name__}.log',
            maxBytes=10240,
            backupCount=10,
            encoding='utf-8'
        )
        file_handler.setFormatter(
            logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            )
        )
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info(f'{__name__} startup')

    with app.app_context():
        listen(db.engine, 'connect', load_extension)

    return app

from app import models
