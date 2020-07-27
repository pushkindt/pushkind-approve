from flask import Flask, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import logging
from logging.handlers import RotatingFileHandler
import os
from sqlalchemy.event import listen
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.PerformLogin'
login.login_message = 'Пожалуйста, авторизуйтесь, чтобы увидеть эту страницу.'
db_collate = 'ru_RU.UTF-8'

def load_extension(dbapi_conn, unused):
	dbapi_conn.enable_load_extension(True)
	dbapi_conn.load_extension(current_app.config['ICU_EXTENSION_PATH'])
	dbapi_conn.enable_load_extension(False)
	dbapi_conn.execute("SELECT icu_load_collation(?, 'ICU_EXT_1')", (db_collate,))

def create_app(config_class=Config):
	app = Flask(__name__)
	app.config.from_object(config_class)
	db.init_app(app)
	migrate.init_app(app, db)
	login.init_app(app)
	
	from app.errors import bp as errors_bp
	app.register_blueprint(errors_bp)

	from app.auth import bp as auth_bp
	app.register_blueprint(auth_bp, url_prefix='/auth')
	
	from app.main import bp as main_bp
	app.register_blueprint(main_bp)

	if not app.debug:
		if not os.path.exists('logs'):
			os.mkdir('logs')
		file_handler = RotatingFileHandler('logs/{}.log'.format(__name__), maxBytes=10240, backupCount=10, encoding='utf-8')
		file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
		file_handler.setLevel(logging.INFO)
		app.logger.addHandler(file_handler)
			
		app.logger.setLevel(logging.INFO)
		app.logger.info('{} startup'.format(__name__))
			
	with app.app_context():
		listen(db.engine, 'connect', load_extension)

	return app

from app import models
