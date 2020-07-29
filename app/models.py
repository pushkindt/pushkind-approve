from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login
from hashlib import md5
from app.ecwid import EcwidAPI
import enum

class UserRoles(enum.IntEnum):
	default = 0
	initiative = 1
	validator = 2
	approver = 3
	admin = 4
	
	def __str__(self):
		pretty = ['Без роли', 'Инициатор', 'Валидатор', 'Согласующий', 'Администратор']
		return pretty[self.value]

@login.user_loader
def load_user(id):
	return User.query.get(int(id))

class Ecwid(db.Model, EcwidAPI):
	id  = db.Column(db.Integer, primary_key = True)

class User(UserMixin, db.Model):
	id  = db.Column(db.Integer, primary_key = True)
	email	= db.Column(db.String(120), index = True, unique = True, nullable=False)
	password = db.Column(db.String(128), nullable=False)
	role = db.Column(db.Enum(UserRoles), nullable=False, default = UserRoles.default)
	name = db.Column(db.String(120))
	phone = db.Column(db.String(120))
	ecwid_id = db.Column(db.Integer, db.ForeignKey('ecwid.id'))
	ecwid = db.relationship('Ecwid')
	
	def __repr__(self):
		return '<User {} role: {}>'.format(self.email, self.role)
	
	def SetPassword(self, password):
		self.password = generate_password_hash(password)
		
	def CheckPassword(self, password):
		return check_password_hash(self.password, password)
		
	def GetAvatar(self, size):
		digest = md5(self.email.lower().encode('utf-8')).hexdigest()
		return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, size)
		
	def to_dict(self):
		data = {'id':self.id, 'email':self.email}
		return data
	
class OrderApproval(db.Model):
	order_id  = db.Column(db.Integer, primary_key = True)
	product_id  = db.Column(db.Integer, primary_key = True)
	approved = db.Column(db.Boolean, nullable=False, default = False)
	comment = db.Column(db.String(120))
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
	