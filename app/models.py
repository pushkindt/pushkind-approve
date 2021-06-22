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
		pretty = ['комментарий', 'согласовано', 'отклонено', 'изменено', 'заявка дублирована', 'отправлена поставщикам', 'экспортирована в 1С']
		return pretty[self.value]
	def color(self):
		colors = ['warning', 'success', 'danger', 'primary', 'primary', 'info', 'info']
		return colors[self.value]


class UserRoles(enum.IntEnum):
	default = 0
	admin = 1
	initiative = 2
	validator = 3
	purchaser = 4
	supervisor = 5
	
	def __str__(self):
		pretty = ['Без роли', 'Администратор', 'Инициатор', 'Валидатор', 'Закупщик', 'Наблюдатель']
		return pretty[self.value]


class OrderStatus(enum.IntEnum):
	new = 0
	not_approved = 1
	partly_approved = 2
	approved = 3
	modified = 4
	
	def __str__(self):
		pretty = ['Новая', 'Отклонена', 'В работе', 'Согласована', 'Исправлена']
		return pretty[self.value]
		
	def color(self):
		colors = ['white', 'danger', 'warning', 'success', 'secondary']
		return colors[self.value]


@login.user_loader
def load_user(id):
	return User.query.get(int(id))


class Ecwid(db.Model, EcwidAPI):
	hub_id = db.Column(db.Integer, db.ForeignKey('ecwid.id'), nullable=True)
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
	role = db.Column(db.Enum(UserRoles), index=True, nullable=False, default=UserRoles.default, server_default='default')
	name = db.Column(db.String(128), nullable=True)
	phone = db.Column(db.String(128), nullable=True)
	position_id = db.Column(db.Integer, db.ForeignKey('position.id'), nullable=True)
	position = db.relationship('Position')
	location = db.Column(db.String(128), nullable=True)
	hub_id = db.Column(db.Integer, db.ForeignKey('ecwid.id'), nullable=True)
	hub = db.relationship('Ecwid')
	email_new = db.Column(db.Boolean, nullable=False, default=True, server_default=expression.true())
	email_modified = db.Column(db.Boolean, nullable=False, default=True, server_default=expression.true())
	email_disapproved = db.Column(db.Boolean, nullable=False, default=True, server_default=expression.true())
	email_approved = db.Column(db.Boolean, nullable=False, default=True, server_default=expression.true())
	last_seen = db.Column(db.DateTime, nullable=True)
	categories = db.relationship('Category', secondary = 'user_category')
	projects = db.relationship('Project', secondary = 'user_project')
	events = db.relationship('OrderEvent', cascade="all, delete-orphan")
	approvals = db.relationship('OrderApproval', cascade="all, delete-orphan", lazy='dynamic')
	orders = db.relationship('Order', cascade="all, delete-orphan")
	note = db.Column(db.String(), nullable=True)

	@property
	def projects_list(self):
		return [p.id for p in self.projects]	
	@property
	def categories_list(self):
		return [c.id for c in self.categories]
	
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
		data = {'id':self.id, \
				'email':self.email, \
				'phone':self.phone if self.phone is not None else '', \
				'note': self.note,
				'role': self.role.name,
				'role_id':int(self.role), \
				'position':self.position.name if self.position is not None else '', \
				'name':self.name if self.name is not None else '', \
				'hub_id':self.hub_id, \
				'location':self.location if self.location is not None else '', \
				'email_new':self.email_new, \
				'email_modified':self.email_modified, \
				'email_disapproved':self.email_disapproved, \
				'email_approved':self.email_approved, \
				'projects':self.projects_list, \
				'categories':self.categories_list}
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


class Position(db.Model):
	id  = db.Column(db.Integer, primary_key = True, nullable = False)
	name = db.Column(db.String(128), nullable=False, index=True)
	hub_id = db.Column(db.Integer, db.ForeignKey('ecwid.id'), nullable=False)
	hub = db.relationship('Ecwid')
	users = db.relationship('User')

class OrderApproval(db.Model):
	id  = db.Column(db.Integer, primary_key = True, nullable=False)
	order_id = db.Column(db.String(128), db.ForeignKey('order.id'), nullable=False)
	product_id  = db.Column(db.Integer, index=True, nullable=True)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
	user = db.relationship('User')
	
	def __bool__(self):
		return self.product_id is None


class Category(db.Model):
	id  = db.Column(db.Integer, primary_key = True, nullable=False)
	name = db.Column(db.String(128), nullable=False, index=True)
	children = db.Column(JsonType(), nullable=False)
	hub_id = db.Column(db.Integer, db.ForeignKey('ecwid.id'), nullable=False)
	hub = db.relationship('Ecwid')
	
	def __hash__(self):
		return self.id
		
	def __eq__(self, another):
		return isinstance(another, Category) and self.id == another.id


class AppSettings(db.Model):
	id  = db.Column(db.Integer, primary_key = True, nullable=False)
	hub_id = db.Column(db.Integer, db.ForeignKey('ecwid.id'), nullable=False, unique=True)
	notify_1C = db.Column(db.Boolean, nullable=False, default=True, server_default=expression.true())
	email_1C =  db.Column(db.String(128), nullable=True)
	hub = db.relationship('Ecwid')


class OrderEvent(db.Model):
	id  = db.Column(db.Integer, primary_key = True, nullable=False)
	order_id = db.Column(db.String(128), db.ForeignKey('order.id'), nullable=False)
	order = db.relationship('Order')
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
	user = db.relationship('User')
	timestamp = db.Column(db.DateTime, nullable=False, default=datetime.now(tz = timezone.utc), server_default=func.datetime('now'))
	type = db.Column(db.Enum(EventType), nullable=False, default=EventType.comment)
	data = db.Column(db.String(), nullable=False, default='', server_default='')


class Project(db.Model):
	id  = db.Column(db.Integer, primary_key = True, nullable=False)
	name = db.Column(db.String(128), nullable=False, index=True)
	hub_id = db.Column(db.Integer, db.ForeignKey('ecwid.id'), nullable=False)
	hub = db.relationship('Ecwid')
	sites = db.relationship('Site', cascade="all, delete-orphan")

	def __repr__(self):
		return json.dumps(self.to_dict())

	def to_dict(self):
		data = {'id':self.id, 'name':self.name, 'sites':[site.to_dict() for site in self.sites]}
		return data


class Site(db.Model):
	id  = db.Column(db.Integer, primary_key = True, nullable=False)
	name = db.Column(db.String(128), nullable=False, index=True)
	project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
	project = db.relationship('Project')

	def to_dict(self):
		data = {'id':self.id, 'project_id':self.project_id, 'name':self.name}
		return data



class Order(db.Model):
	id  = db.Column(db.String(128), primary_key = True, nullable=False)
	initiative_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
	initiative = db.relationship('User')
	create_timestamp = db.Column(db.Integer, nullable=False)
	products = db.Column(JsonType(), nullable=False)
	total  = db.Column(db.Float, nullable=False)
	status = db.Column(db.Enum(OrderStatus), nullable=False, default=OrderStatus.new, server_default='new')
	site_id = db.Column(db.Integer, db.ForeignKey('site.id'), nullable=True)
	site = db.relationship('Site')
	income_statement = db.Column(db.String(128), nullable=True) #БДР
	cash_flow_statement = db.Column(db.String(128), nullable=True) #БДДС
	categories = db.relationship('Category', secondary = 'order_category')
	hub_id = db.Column(db.Integer, db.ForeignKey('ecwid.id'), nullable=False)
	hub = db.relationship('Ecwid')
	events = db.relationship('OrderEvent', cascade="all, delete-orphan")
	purchased = db.Column(db.Boolean, nullable=False, default=False, server_default=expression.false())
	exported = db.Column(db.Boolean, nullable=False, default=False, server_default=expression.false())
	positions = db.relationship('Position', secondary = 'order_position')
	approvals = db.relationship('OrderPosition')
	user_approvals = db.relationship('OrderApproval')
	positions = db.relationship('Position', secondary = 'order_position')
	
	parents = db.relationship(
		'Order',
		secondary='order_relationship',
		primaryjoin='Order.id == OrderRelationship.child_id',
		secondaryjoin='Order.id == OrderRelationship.parent_id',
		backref=db.backref('children')
	)

	def UpdateOrderStatus(self):
		disapproved = OrderApproval.query.filter(OrderApproval.order_id == self.id, OrderApproval.product_id != None).all()
		if len(disapproved) > 0:
			self.status = OrderStatus.not_approved
			return
		approved = [p.approved for p in self.approvals]
		if all(approved):
			self.status = OrderStatus.approved
			return
		self.status = OrderStatus.partly_approved
		return

	@property
	def categories_list(self):
		return [c.id for c in self.categories]
		
	@property
	def reviewers(self):
		return User.query.filter_by(role = UserRoles.validator).join(Position).join(OrderPosition).filter_by(order_id = self.id).all()
		
	@classmethod
	def UpdateOrdersPositions(cls, hub_id, order_id = None):
	
		orders = Order.query.filter(Order.hub_id == hub_id, Order.status != OrderStatus.approved)
		if order_id is not None:
			orders = orders.filter_by(id = order_id)
	
		for order in orders.all():
			if order.site is None or len(order.categories) == 0:
				continue
			positions = Position.query.filter_by(hub_id = hub_id)
			positions = positions.join(User).filter(User.role == UserRoles.validator)
			positions = positions.join(UserCategory, User.id == UserCategory.user_id).filter(UserCategory.category_id.in_(order.categories_list))
			positions = positions.join(UserProject, User.id == UserProject.user_id).filter(UserProject.project_id == order.site.project_id)
			order.positions = positions.all()
			approvals = positions.join(OrderApproval).filter(OrderApproval.order_id == order.id, OrderApproval.product_id == None).all()
			for approval in approvals:
				db.session.query(OrderPosition).filter(OrderPosition.order_id == order.id, OrderPosition.position_id == approval.id).\
				update({OrderPosition.approved: True})
		db.session.commit()
	
	@property
	def create_date(self):
		return datetime.fromtimestamp(self.create_timestamp, tz=timezone.utc)
		
	@create_date.setter
	def create_date(self, dt):
		self.create_timestamp = int(dt.timestamp())
		
	def to_ecwid(self):
		data = {'email':self.initiative.email, \
				'items':self.products, \
				'total':self.total, \
				'paymentStatus':'AWAITING_PAYMENT', \
				'fulfillmentStatus':'AWAITING_PROCESSING'
				}
		return data

class OrderCategory(db.Model):
	__tablename__ = 'order_category'
	order_id = db.Column(db.String(128), db.ForeignKey('order.id', ondelete='CASCADE'), primary_key = True)
	category_id = db.Column(db.Integer, db.ForeignKey('category.id', ondelete='CASCADE'), primary_key = True)
	
class OrderRelationship(db.Model):
	__tablename__ = 'order_relationship'
	parent_id = db.Column(db.String(128), db.ForeignKey('order.id', ondelete='CASCADE'), primary_key = True)
	child_id = db.Column(db.String(128), db.ForeignKey('order.id', ondelete='CASCADE'), primary_key = True)
	
class OrderPosition(db.Model):
	__tablename__ = 'order_position'
	order_id = db.Column(db.String(128), db.ForeignKey('order.id', ondelete='CASCADE'), primary_key = True)
	position_id = db.Column(db.Integer, db.ForeignKey('position.id', ondelete='CASCADE'), primary_key = True)
	approved = db.Column(db.Boolean, nullable=False, default=False, server_default=expression.false())
	position = db.relationship('Position')
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
	user = db.relationship(User)
	timestamp = db.Column(db.DateTime, nullable=True)

class UserCategory(db.Model):
	__tablename__ = 'user_category'
	user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), primary_key = True)
	category_id = db.Column(db.Integer, db.ForeignKey('category.id', ondelete='CASCADE'), primary_key = True)

class UserProject(db.Model):
	__tablename__ = 'user_project'
	user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), primary_key = True)
	project_id = db.Column(db.Integer, db.ForeignKey('project.id', ondelete='CASCADE'), primary_key = True)
	
	