from flask_wtf import FlaskForm
from wtforms import SubmitField, IntegerField, StringField, SelectField, TextAreaField, FormField, Form, PasswordField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, Length, ValidationError, Email, InputRequired, Optional
from app.models import UserRoles
from flask_login import current_user


class AddStoreForm(FlaskForm):
	name = StringField('Поставщик', validators = [DataRequired(message='Название поставщика - обязательное поле.')])
	email = EmailField('Электронная почта', validators = [DataRequired(message='Электронная почта - обязательное поле.'), Email()])
	password = PasswordField('Пароль', validators = [DataRequired(message='Пароль - обязательное поле.')])
	plan = StringField('Платежный план', default = 'J_PUSHKIND_FREEDEMO', validators = [DataRequired(message='Платежный план - обязательное поле.')])
	submit = SubmitField('Создать')

class EcwidSettingsForm(FlaskForm):
	partners_key  = StringField('Ключ partners_key', [DataRequired(message = 'Ключ partners_key - обязательное поле')])
	client_id     = StringField('Ключ client_id', [DataRequired(message = 'Ключ client_id - обязательное поле')])
	client_secret = StringField('Ключ client_secret', [DataRequired(message = 'Ключ client_secret - обязательное поле')])
	store_id      = IntegerField('ID магазина', [DataRequired(message = 'ID магазина - обязательное поле')])
	submit1       = SubmitField('Сохранить')

class UserSettings(Form):
	full_name  = StringField('Имя', [DataRequired(message = 'Имя - обязательное поле')])
	phone = StringField('Телефон')
	location = StringField('Площадка')
	position = StringField('Должность')
	
	def validate_location(self, location):
		if current_user.role == UserRoles.initiative and (location.data == None or location.data.strip() == ''):
			raise ValidationError('Площадка - обязательное поле')
	

class UserRolesForm(FlaskForm):
	user_id = SelectField('Идентификатор пользователя',[DataRequired(message = 'Некорректный идентификатор пользователя')], coerce = int)
	role = SelectField('Роль',[InputRequired(message = 'Некорректная роль пользователя')], coerce = int,
						choices = [(int(role), str(role)) for role in UserRoles])
	about_user = FormField(UserSettings, [DataRequired()])
	submit2 = SubmitField('Сохранить')

	def validate_role(self, role):
		if UserRoles(role.data) == UserRoles.initiative and (self.about_user.location.data == None or self.about_user.location.data.strip() == ''):
			raise ValidationError('Площадка - обязательное поле')
	
class UserSettingsForm(FlaskForm):
	about_user = FormField(UserSettings, [DataRequired()])
	submit3 = SubmitField('Сохранить')
	
class OrderCommentsForm(FlaskForm):
	comment  = TextAreaField('Комментарий', [InputRequired(message = 'Комментарий не может быть пустым'), Length(max = 256, message = 'Слишком длинный комментарий')])
	submit1 = SubmitField('Сохранить')
	
class OrderApprovalForm(FlaskForm):
	product_id    = IntegerField('Идентификатор товара', render_kw={'hidden': ''})
	product_sku   = StringField('Артикул товара', render_kw={'hidden': ''})
	submit = SubmitField('Сохранить')
	
class ChangeQuantityForm(FlaskForm):
	product_id    = IntegerField('Идентификатор товара', [DataRequired(message = 'ID товара - обязательное поле')], render_kw={'hidden': ''})
	product_quantity   = IntegerField('Количество товара', [InputRequired(message = 'Невозможное значение количества')], render_kw={'type': 'number', 'step' : 1, 'min' : 0})
	
	def validate_product_quantity(self, product_quantity):
		if product_quantity.data < 0:
			raise ValidationError('Количество не может быть меньше нуля.')