from flask_wtf import FlaskForm
from wtforms import SubmitField, IntegerField, StringField, SelectField, TextAreaField, FormField, Form, PasswordField, BooleanField, SelectMultipleField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, Length, ValidationError, Email, InputRequired, Optional
from app.models import UserRoles
from wtforms.fields.html5 import DateField
from app.main.utils import DATE_FORMAT
from datetime import date
import json


class JSONField(StringField):
    def _value(self):
        return json.dumps(self.data) if self.data else ''

    def process_formdata(self, valuelist):
        if valuelist:
            try:
                self.data = json.loads(valuelist[0])
            except ValueError:
                raise ValueError('Не корректное поле данных.')
        else:
            self.data = None

    def pre_validate(self, form):
        super().pre_validate(form)
        if self.data:
            try:
                json.dumps(self.data)
            except TypeError:
                raise ValueError('Не корректное поле данных.')


'''
################################################################################
Approve page
################################################################################
'''


class InitiativeForm(FlaskForm):
    project = SelectField('Проект', validators=[DataRequired(message='Название проекта - обязательное поле.')],
                          coerce=int)
    site = SelectField('Объект', validators=[DataRequired(message='Название проекта - обязательное поле.')],
                       coerce=int)
    categories = SelectMultipleField('Категории', validators=[DataRequired(
        message='Категории заявки - обязательное поле.')], coerce=int)
    submit = SubmitField('Сохранить')


class ApproverForm(FlaskForm):
    income_statement = SelectField(
        'Статья БДР', [DataRequired(message='Статья БДР - обязательное поле.')], coerce=int)
    cashflow_statement = SelectField(
        'Статья БДДС', [DataRequired(message='Статья БДДС - обязательное поле.')], coerce=int)
    submit = SubmitField('Сохранить')


class LeaveCommentForm(FlaskForm):
    comment = TextAreaField('Комментарий', [InputRequired(
        message='Комментарий не может быть пустым'), Length(max=256, message='Слишком длинный комментарий.')])
    submit = SubmitField('Сохранить')


class OrderApprovalForm(FlaskForm):
    product_id = IntegerField('Идентификатор товара', render_kw={'hidden': ''})
    comment = TextAreaField('Замечание', [Length(
        max=256, message='Слишком длинное замечание.')])
    submit = SubmitField('Сохранить')


class ChangeQuantityForm(FlaskForm):
    product_id = IntegerField('Идентификатор товара', [DataRequired(
        message='ID товара - обязательное поле.')], render_kw={'hidden': ''})
    product_quantity = IntegerField('Количество товара', [InputRequired(
        message='Невозможное значение количества.')], render_kw={'type': 'number', 'step': 1, 'min': 0})
    product_measurement = StringField('Единица измерения', [Length(
        max=10, message='Единицы измерения должны быть аббревиатурой.')])
    submit = SubmitField('Сохранить')

    def validate_product_quantity(self, product_quantity):
        if product_quantity.data < 0:
            raise ValidationError('Количество не может быть меньше нуля.')

class SplitOrderForm(FlaskForm):
    products = JSONField('products', [InputRequired(
        message='Список позиций не может быть пустым.')])
    submit = SubmitField('Разделить')

'''
################################################################################
Stores page
################################################################################
'''


class AddStoreForm(FlaskForm):
    name = StringField('Поставщик', validators=[DataRequired(
        message='Название поставщика - обязательное поле.')])
    email = EmailField('Электронная почта', validators=[DataRequired(
        message='Электронная почта - обязательное поле.'), Email()])
    password = PasswordField('Пароль', validators=[
                             DataRequired(message='Пароль - обязательное поле.')])
    plan = StringField('Платежный план', default='J_PUSHKIND_FREEDEMO', validators=[
                       DataRequired(message='Платежный план - обязательное поле.')])
    submit = SubmitField('Создать')


'''
################################################################################
Settings page
################################################################################
'''


class UserSettings(Form):
    full_name = StringField(
        'Имя', [DataRequired(message='Имя - обязательное поле.')])
    phone = StringField('Телефон')
    categories = SelectMultipleField('Мои категории ↓', coerce=int)
    projects = SelectMultipleField('Мои проекты ↓', coerce=int)
    position = StringField(
        'Роль', [InputRequired(message='Роль - обязательное поле.')])
    location = StringField('Площадка')
    email_new = BooleanField('Новые заявки')
    email_modified = BooleanField('Заявка изменена')
    email_disapproved = BooleanField('Заявка отклонена')
    email_approved = BooleanField('Заявка согласована')


class UserRolesForm(FlaskForm):
    user_id = IntegerField('Идентификатор пользователя',
                           render_kw={'hidden': ''})
    role = SelectField('Права доступа', [InputRequired(message='Некорректные права доступа пользователя.')], coerce=int,
                       choices=[(int(role), str(role)) for role in UserRoles])
    about_user = FormField(UserSettings, [DataRequired()])
    note = TextAreaField('Заметка')
    submit = SubmitField('Сохранить')


class UserSettingsForm(FlaskForm):
    about_user = FormField(UserSettings, [DataRequired()])
    submit = SubmitField('Сохранить')


'''
################################################################################
Index page
################################################################################
'''


class MergeOrdersForm(FlaskForm):
    orders = JSONField('orders', [InputRequired(
        message='Список заявок не может быть пустым.')])
    submit = SubmitField('Объединить')


class SaveOrdersForm(FlaskForm):
    orders = JSONField('orders', [InputRequired(
        message='Список заявок не может быть пустым.')])


'''
################################################################################
Admin page
################################################################################
'''


class EcwidSettingsForm(FlaskForm):
    partners_key = StringField('Ключ partners_key', [DataRequired(
        message='Ключ partners_key - обязательное поле.')])
    client_id = StringField('Ключ client_id', [DataRequired(
        message='Ключ client_id - обязательное поле.')])
    client_secret = StringField('Ключ client_secret', [DataRequired(
        message='Ключ client_secret - обязательное поле.')])
    store_id = IntegerField('ID магазина', [DataRequired(
        message='ID магазина - обязательное поле.')])
    submit = SubmitField('Сохранить')


class Notify1CSettingsForm(FlaskForm):
    email = EmailField('Электронная почта')
    enable = BooleanField('Включить рассылку 1С')
    submit = SubmitField('Сохранить')


class AddProjectForm(FlaskForm):
    project_name = StringField('Название', validators=[DataRequired(
        message='Название проекта - обязательное поле.')])
    uid = StringField('Код', validators=[Optional()])
    submit = SubmitField('Добавить')


class AddSiteForm(FlaskForm):
    project_id = IntegerField('ID проекта', [DataRequired(
        message='ID проекта - обязательное поле.')])
    site_name = StringField('Название', validators=[DataRequired(
        message='Название объекта - обязательное поле.')])
    uid = StringField('Код', validators=[Optional()])
    submit = SubmitField('Добавить')


class EditProjectForm(FlaskForm):
    project_id = IntegerField('ID проекта', [DataRequired(
        message='ID проекта - обязательное поле.')])
    project_name = StringField('Название', validators=[DataRequired(
        message='Название проекта - обязательное поле.')])
    uid = StringField('Код', validators=[Optional()])
    enabled = BooleanField('Включить проект')
    submit = SubmitField('Изменить')


class EditSiteForm(FlaskForm):
    site_id = IntegerField('ID проекта', [DataRequired(
        message='ID проекта - обязательное поле.')])
    site_name = StringField('Название', validators=[DataRequired(
        message='Название объекта - обязательное поле.')])
    uid = StringField('Код', validators=[Optional()])
    submit = SubmitField('Изменить')


class CategoryResponsibilityForm(FlaskForm):
    category_id = IntegerField('ID категории', [DataRequired(
        message='ID категории - обязательное поле.')])
    responsible = StringField('Ответственный', validators=[DataRequired(
        message='Ответственный - обязательное поле.')])
    functional_budget = StringField('Функциональный бюджет', validators=[DataRequired(
        message='Функциональный бюджет - обязательное поле.')])
    income_statement = SelectField(
        'Статья БДР', [DataRequired(message='Статья БДР - обязательное поле.')], coerce=int)
    cashflow_statement = SelectField(
        'Статья БДДС', [DataRequired(message='Статья БДДС - обязательное поле.')], coerce=int)
    code = StringField('Код', validators=[DataRequired(
        message='Код категории - обязательное поле.')])
    submit = SubmitField('Сохранить')
    
 
class AddIncomeForm(FlaskForm):
    income_name = StringField('БДР', validators=[DataRequired(
        message='БДР - обязательное поле.')])
    submit = SubmitField('Добавить')
    
class AddCashflowForm(FlaskForm):
    cashflow_name = StringField('БДДС', validators=[DataRequired(
        message='БДДС - обязательное поле.')])
    submit = SubmitField('Добавить')
    
class EditIncomeForm(FlaskForm):
    income_id = IntegerField('ID БДР', [DataRequired(
        message='ID БДР - обязательное поле.')])
    income_name = StringField('БДР', validators=[DataRequired(
        message='БДР - обязательное поле.')])
    submit = SubmitField('Изменить')
    
class EditCashflowForm(FlaskForm):
    cashflow_id = IntegerField('ID БДДС', [DataRequired(
        message='ID БДДС - обязательное поле.')])
    cashflow_name = StringField('БДДС', validators=[DataRequired(
        message='БДДС - обязательное поле.')])
    submit = SubmitField('Изменить')