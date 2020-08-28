from flask_wtf import FlaskForm
from wtforms import PasswordField, BooleanField, SubmitField, StringField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from wtforms.fields.html5 import EmailField
from app.models import User

class LoginForm(FlaskForm):
	email = EmailField('Электронная почта', validators = [DataRequired(message='Электронная почта - обязательное поле.'), Email()])
	password = PasswordField('Пароль', validators = [DataRequired(message='Пароль - обязательное поле.')])
	remember_me = BooleanField('Запомнить меня')
	submit = SubmitField('Авторизация')
	
class RegistrationForm(FlaskForm):
	email = EmailField('Электронная почта', validators = [DataRequired(message='Электронная почта - обязательное поле.'), Email()])
	password = PasswordField('Пароль', validators = [DataRequired(message='Пароль - обязательное поле.')])
	password2 = PasswordField('Повторите пароль', validators = [DataRequired(), EqualTo('password', message = 'Пароли не совпадают.')])
	submit = SubmitField('Регистрация')
	
	def validate_email(self, email):
		user = User.query.filter_by(email=self.email.data).first()
		if user is not None:
			raise ValidationError('Этот адрес электронной почты уже занят.')
			
class ResetPasswordRequestForm(FlaskForm):
	email = StringField('Электронная почта', validators=[DataRequired(message='Электронная почта - обязательное поле.'), Email()])
	submit = SubmitField('Сбросить')
	
class ResetPasswordForm(FlaskForm):
	password = PasswordField('Пароль', validators = [DataRequired(message='Пароль - обязательное поле.')])
	password2 = PasswordField('Повторите пароль', validators = [DataRequired(), EqualTo('password', message = 'Пароли не совпадают.')])
	submit = SubmitField('Сменить')