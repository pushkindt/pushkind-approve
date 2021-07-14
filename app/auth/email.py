from flask import render_template, current_app
from app.email import SendEmail


def SendPasswordResetEmail(user):
    token = user.GetPasswordResetToken()
    SendEmail('Сброс пароля для "Согласования заявок"',
              sender=current_app.config['MAIL_USERNAME'],
              recipients=[user.email],
              text_body=render_template('email/reset.txt', token=token),
              html_body=render_template('email/reset.html', token=token))


def SendUserRegisteredEmail(user):
    SendEmail('Зарегистрирован новый пользователь',
              sender=current_app.config['MAIL_USERNAME'],
              recipients=[current_app.config['ADMIN_EMAIL']],
              text_body=render_template('email/registered.txt', user=user),
              html_body=render_template('email/registered.html', user=user))
