from flask_wtf import FlaskForm
from wtforms import SubmitField, IntegerField, StringField, SelectField, TextAreaField, FormField, Form, PasswordField, BooleanField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, Length, ValidationError, Email, InputRequired, Optional
from app.models import UserRoles
from wtforms.fields.html5 import DateField
from app.main.utils import DATE_FORMAT
from datetime import date

class AddRemoveLocationForm(FlaskForm):
	location_name = StringField('Площадка', validators = [DataRequired(message='Название площадки - обязательное поле.')])
	site_name = StringField('Объект', validators = [Optional()])
	submit1 = SubmitField('Добавить')
	submit2 = SubmitField('Удалить')
	
class ChangeLocationForm(FlaskForm):
	location_name = SelectField('Площадка', validators = [DataRequired(message='Название площадки - обязательное поле.')],
						coerce=int)
	submit = SubmitField('Сохранить')

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
	user_data = StringField('Параметры')
	position = StringField('Роль')
	email_new = BooleanField('Новые заявки')
	email_modified = BooleanField('Заявка изменена')
	email_disapproved = BooleanField('Заявка отклонена')
	email_approved = BooleanField('Заявка согласована')

class UserRolesForm(FlaskForm):
	user_id = SelectField('Идентификатор пользователя',[DataRequired(message = 'Некорректный идентификатор пользователя')], coerce = int)
	role = SelectField('Права доступа',[InputRequired(message = 'Некорректные права доступа пользователя')], coerce = int,
						choices = [(int(role), str(role)) for role in UserRoles])
	about_user = FormField(UserSettings, [DataRequired()])
	submit2 = SubmitField('Сохранить')
	
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

class Export1CReport(FlaskForm):
	date = DateField('Дата поставки', [InputRequired(message = 'Дата поставки - обязательное поле.')], format=DATE_FORMAT, default = date.today())
	send_email = BooleanField('Отправить на zayavka@velesstroy.com')
	submit = SubmitField('Выгрузить')

class BECForm(FlaskForm):
	bec = StringField('Статья БДР', [InputRequired(message = 'Статья БДР - обязательное поле.')])
	submit = SubmitField('Сохранить')
	
class CFSForm(FlaskForm):
	cfs = StringField('Статья БДДС', [InputRequired(message = 'Статья БДДС - обязательное поле.')])
	submit = SubmitField('Сохранить')
	
class SiteForm(FlaskForm):
	object = StringField('Объект', [InputRequired(message = 'Название объекта - обязательное поле.')])
	submit = SubmitField('Сохранить')
	
class MergeOrdersForm(FlaskForm):
	orders = StringField('orders', [InputRequired(message = 'Список заявок не может быть пустым.')])
	submit = SubmitField('Объединить')