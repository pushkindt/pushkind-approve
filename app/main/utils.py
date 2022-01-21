from functools import wraps

from flask import current_app
from flask_login import current_user
from flask import render_template, flash, jsonify

from app import db
from app.models import Order
from app.email import SendEmail


'''
################################################################################
Consts
################################################################################
'''
DATE_TIME_FORMAT = '%Y-%m-%d %H:%M:%S %z'
DATE_FORMAT = '%Y-%m-%d'

'''
################################################################################
Utilities
################################################################################
'''


def role_required(roles_list):
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            if current_user.role not in roles_list:
                return render_template('errors/403.html'), 403
            else:
                return function(*args, **kwargs)
        return wrapper
    return decorator


def role_forbidden(roles_list):
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            if current_user.role in roles_list:
                return render_template('errors/403.html'), 403
            else:
                return function(*args, **kwargs)
        return wrapper
    return decorator


def role_required_ajax(roles_list):
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            if current_user.role not in roles_list:
                return jsonify({'status': False, 'flash': ['У вас нет соответствующих полномочий.']}), 403
            else:
                return function(*args, **kwargs)
        return wrapper
    return decorator


def role_forbidden_ajax(roles_list):
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            if current_user.role in roles_list:
                return jsonify({'status': False, 'flash': ['У вас нет соответствующих полномочий.']}), 403
            else:
                return function(*args, **kwargs)
        return wrapper
    return decorator


def ecwid_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if current_user.hub is None:
            flash('Взаимодействие с ECWID не настроено.')
            return render_template('errors/400.html'), 400
        else:
            return function(*args, **kwargs)
    return wrapper


def ecwid_required_ajax(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if current_user.hub is None:
            return jsonify({'status': False, 'flash': ['Взаимодействие с ECWID не настроено.']}), 400
        else:
            return function(*args, **kwargs)
    return wrapper


def SendEmailNotification(type, order):
    recipients = [reviewer.email for reviewer in order.reviewers if getattr(
        reviewer, 'email_{}'.format(type), False) == True]
    if getattr(order.initiative, 'email_{}'.format(type), False) == True:
        recipients.append(order.initiative.email)
    current_app.logger.info('"{}" email about order {} has been sent to {}'.format(
        type, order.id, recipients))
    if len(recipients) > 0:
        SendEmail('Уведомление по заявке #{}'.format(order.id),
                  sender=current_app.config['MAIL_USERNAME'],
                  recipients=recipients,
                  text_body=render_template(
                      'email/{}.txt'.format(type), order=order),
                  html_body=render_template('email/{}.html'.format(type), order=order))


def SendEmail1C(recipients, order, data):
    current_app.logger.info(
        '"export1C" email about order {} has been sent to {}'.format(order.id, recipients))
        
    if order.site is not None:
        subject = '{}. {} (pushkind_{})'.format(order.site.project.name, order.site.name, order.id)
    else:
        subject = 'pushkind_{}'.format(order.id)
        
    data = ('pushkind_{}.xlsx'.format(order.id), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', data)
        
    SendEmail(subject,
              sender=current_app.config['MAIL_USERNAME'],
              recipients=recipients,
              text_body=render_template('email/export1C.txt', order=order),
              html_body=render_template('email/export1C.html', order=order),
              attachments=[data])


def GetNewOrderNumber():
    count = db.session.query(Order).count()
    letter = chr(int(count / 1000) + 97)
    count = count % 1000
    return f'{letter}{count:04d}'