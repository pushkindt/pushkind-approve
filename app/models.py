from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login
from hashlib import md5
from app.ecwid import EcwidAPI
import enum
import json
import jwt
from time import time
from flask import current_app
from datetime import datetime, timezone
from sqlalchemy.sql import func
from sqlalchemy.types import TypeDecorator
from json.decoder import JSONDecodeError
from sqlalchemy.sql import expression


class EventType(enum.IntEnum):
	comment = 0
	approved = 1
	disapproved = 2
	modified = 3
	duplicated = 4
	vendor = 5
	export1C = 6

	def __str__(self):
		pretty = ['оставлен комментарий', 'согласовано', 'отклонено', 'изменено', 'заявка дублирована', 'отправлена поставщикам', 'экспортирована в 1С']
		return pretty[self.value]
	def color(self):
		colors = ['warning', 'success', 'danger', 'primary', 'primary', 'info', 'info']
		return colors[self.value]

class UserRoles(enum.IntEnum):
	default = 0
	initiative = 1
	validator = 2
	approver = 3
	admin = 4
	
	def __str__(self):
		pretty = ['Без роли', 'Инициатор', 'Валидатор', 'Закупщик', 'Администратор']
		return pretty[self.value]
		
class OrderStatus(enum.IntEnum):
	new = 0
	not_approved = 1
	partly_approved = 2
	approved = 3
	modified = 4
	
	def __str__(self):
		pretty = ['Новая', 'Не согласована', 'В работе', 'Согласована', 'Исправлена']
		return pretty[self.value]
		
	def color(self):
		colors = ['secondary', 'danger', 'warning', 'success', 'primary']
		return colors[self.value]

@login.user_loader
def load_user(id):
	return User.query.get(int(id))

class Ecwid(db.Model, EcwidAPI):
	id  = db.Column(db.Integer, primary_key=True)
	ecwid_id = db.Column(db.Integer, db.ForeignKey('ecwid.id'))
	hub = db.relationship('Ecwid')

class JsonType(TypeDecorator):
	impl = db.String()

	def process_bind_param(self, value, dialect):
		if value is not None:
			return json.dumps(value)
		else:
			return None
		
	def process_result_value(self, value, dialect):
		try:
			result = json.loads(value)
			return result
		except (JSONDecodeError, TypeError):
			return None

class User(UserMixin, db.Model):
	id  = db.Column(db.Integer, primary_key=True, nullable=False)
	email	= db.Column(db.String(128), index=True, unique=True, nullable=False)
	password = db.Column(db.String(128), nullable=False)
	role = db.Column(db.Enum(UserRoles), index=True, nullable=False, default=UserRoles.default)
	name = db.Column(db.String(128), nullable=False, default='', server_default='')
	phone = db.Column(db.String(128), nullable=False, default='', server_default='')
	position = db.Column(db.String(128), nullable=False, default='', server_default='')
	data = db.Column(JsonType())
	ecwid_id = db.Column(db.Integer, db.ForeignKey('ecwid.id'), nullable=True, index=True)
	hub = db.relationship('Ecwid')
	email_new = db.Column(db.Boolean, nullable=False, default=True, server_default=expression.true())
	email_modified = db.Column(db.Boolean, nullable=False, default=True, server_default=expression.true())
	email_disapproved = db.Column(db.Boolean, nullable=False, default=True, server_default=expression.true())
	email_approved = db.Column(db.Boolean, nullable=False, default=True, server_default=expression.true())
	
	def __hash__(self):
		return self.id
		
	def __eq__(self, another):
		return isinstance(another, User) and self.id == another.id
	
	def __repr__(self):
		return json.dumps(self.to_dict())

	def SetPassword(self, password):
		self.password = generate_password_hash(password)
		
	def CheckPassword(self, password):
		return check_password_hash(self.password, password)
		
	def GetAvatar(self, size):
		digest = md5(self.email.lower().encode('utf-8')).hexdigest()
		return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, size)
		
	def to_dict(self):
		data = {'id':self.id, 'email':self.email, 'phone':self.phone,\
				'data':self.data, 'role': self.role.name,'role_id':int(self.role),\
				'name':self.name, 'ecwid_id':self.ecwid_id, 'position':self.position,\
				'email_new':self.email_new, 'email_modified':self.email_modified,\
				'email_disapproved':self.email_disapproved, 'email_approved':self.email_approved}
		return data
		
	def GetPasswordResetToken(self, expires_in=600):
		return jwt.encode(
			{'reset_password': self.id, 'exp': time() + expires_in},
			current_app.config['SECRET_KEY'],
			algorithm='HS256').decode('utf-8')

	@staticmethod
	def VerifyPasswordResetToken(token):
		try:
			id = jwt.decode(token, current_app.config['SECRET_KEY'],
							algorithms=['HS256'])['reset_password']
		except:
			return
		return User.query.get(id)
	
class OrderApproval(db.Model):
	id  = db.Column(db.Integer, primary_key = True, nullable=False)
	order_id  = db.Column(db.Integer, index=True, nullable=False)
	product_id  = db.Column(db.Integer, index=True, nullable=True)
	product_sku = db.Column(db.String(128), nullable=True)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True, nullable=False)
	user = db.relationship('User')
	
	def __bool__(self):
		return self.product_id is None
	
class CacheCategories(db.Model):
	id  = db.Column(db.Integer, primary_key = True, nullable=False)
	name = db.Column(db.String(128), nullable=False, index=True)
	children = db.Column(JsonType(), nullable=False)
	ecwid_id = db.Column(db.Integer, db.ForeignKey('ecwid.id'), index=True)
	hub = db.relationship('Ecwid')
	
class ApiData(db.Model):
	id  = db.Column(db.Integer, primary_key = True, nullable=False)
	timestamp = db.Column(db.DateTime, nullable=False, default=datetime.now(tz = timezone.utc), server_default=func.datetime('now'))
	ecwid_id = db.Column(db.Integer, db.ForeignKey('ecwid.id'), nullable=False, index=True, unique=True)
	hub = db.relationship('Ecwid')

class EventLog(db.Model):
	id  = db.Column(db.Integer, primary_key = True, nullable=False)
	user = db.relationship('User')
	order_id  = db.Column(db.Integer, nullable=False)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
	timestamp = db.Column(db.DateTime, nullable=False, default=datetime.now(tz = timezone.utc), server_default=func.datetime('now'))
	type = db.Column(db.Enum(EventType), nullable=False, default=EventType.comment)
	data = db.Column(db.String(), nullable=False, default='', server_default='')
	
class Location(db.Model):
	id  = db.Column(db.Integer, primary_key = True, nullable=False)
	name = db.Column(db.String(128), nullable=False, index=True)
	ecwid_id = db.Column(db.Integer, db.ForeignKey('ecwid.id'), index=True)
	hub = db.relationship('Ecwid')
	sites = db.relationship('Site')

	def __repr__(self):
		return json.dumps(self.to_dict())

	def to_dict(self):
		data = {'id':self.id, 'name':self.name, 'sites':[site.to_dict() for site in self.sites]}
		return data
	
class Site(db.Model):
	id  = db.Column(db.Integer, primary_key = True, nullable=False)
	name = db.Column(db.String(128), nullable=False, index=True)
	loc_id = db.Column(db.Integer, db.ForeignKey('location.id'), index=True)
	location = db.relationship('Location')
	
	def to_dict(self):
		data = {'id':self.id, 'loc_id':self.loc_id, 'name':self.name}
		return data
	