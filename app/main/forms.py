from flask_wtf import FlaskForm
from wtforms import SubmitField, IntegerField, StringField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Length
from app.models import UserRoles

class EcwidSettingsForm(FlaskForm):
	partners_key  = StringField('Ключ partners_key', validators = [DataRequired()])
	client_id     = StringField('Ключ client_id', validators = [DataRequired()])
	client_secret = StringField('Ключ client_secret', validators = [DataRequired()])
	store_id      = IntegerField('ID магазина', validators = [DataRequired()])
	submit1       = SubmitField('Сохранить')
	
class UserRolesForm(FlaskForm):
	user_id = SelectField('Идентификатор пользователя', coerce = int)
	role = SelectField('Роль', coerce = int,
						choices = [
							(int(UserRoles.default), str(UserRoles.default)),
							(int(UserRoles.initiative), str(UserRoles.initiative)),
							(int(UserRoles.validator), str(UserRoles.validator)),
							(int(UserRoles.approver), str(UserRoles.approver)),
							(int(UserRoles.admin), str(UserRoles.admin)),
						])
	submit2 = SubmitField('Сохранить')
	
class UserSettingsForm(FlaskForm):
	name  = StringField('Имя', validators = [DataRequired()])
	phone = StringField('Телефон', validators = [DataRequired()])
	location = StringField('Расположение', validators = [DataRequired()])
	submit3 = SubmitField('Сохранить')
	
class OrderCommentsForm(FlaskForm):
	comment  = TextAreaField('Комментарий', validators = [Length(max = 128)])
	submit = SubmitField('Сохранить')
	
class OrderApprovalForm(FlaskForm):
	product_id    = IntegerField('Идентификатор товара')
	product_sku   = StringField('Артикул товара', validators = [DataRequired()])
	submit = SubmitField('Сохранить')