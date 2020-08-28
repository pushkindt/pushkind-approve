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

class UserRoles(enum.IntEnum):
	default = 0
	initiative = 1
	validator = 2
	approver = 3
	admin = 4
	
	def __str__(self):
		pretty = ['Без роли', 'Инициатор', 'Валидатор', 'Согласующий', 'Администратор']
		return pretty[self.value]
		
class OrderStatus(enum.IntEnum):
	new = 0
	not_approved = 1
	partly_approved = 2
	approved = 3
	
	def __str__(self):
		pretty = ['new', 'not_approved', 'partly_approved', 'approved']
		return pretty[self.value]

@login.user_loader
def load_user(id):
	return User.query.get(int(id))

class Ecwid(db.Model, EcwidAPI):
	id  = db.Column(db.Integer, primary_key=True)
	ecwid_id = db.Column(db.Integer, db.ForeignKey('ecwid.id'))
	hub = db.relationship('Ecwid')

class User(UserMixin, db.Model):
	id  = db.Column(db.Integer, primary_key=True, nullable=False)
	email	= db.Column(db.String(120), index=True, unique=True, nullable=False)
	password = db.Column(db.String(128), nullable=False)
	role = db.Column(db.Enum(UserRoles), index=True, nullable=False, default=UserRoles.default)
	name = db.Column(db.String(120), nullable=False, default='', server_default='')
	phone = db.Column(db.String(120), nullable=False, default='', server_default='')
	location = db.Column(db.String(120), nullable=False, default='', server_default='')
	ecwid_id = db.Column(db.Integer, db.ForeignKey('ecwid.id'), nullable=True, index=True)
	hub = db.relationship('Ecwid')
	
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
		data = {'id':self.id, 'email':self.email, 'phone':self.phone, 'location':self.location, 'role_id':int(self.role), 'name':self.name, 'ecwid_id':self.ecwid_id}
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
	product_sku = db.Column(db.String(120), nullable=True)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True, nullable=False)
	user = db.relationship('User')
	timestamp = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc), server_default=func.datetime('now'))
	
class OrderComment(db.Model):
	user = db.relationship('User')
	order_id  = db.Column(db.Integer, primary_key = True, nullable=False)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, primary_key = True)
	comment = db.Column(db.String(120), nullable=False, default='', server_default='')
	timestamp = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc), server_default=func.datetime('now'))
	
	