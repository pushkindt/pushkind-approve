from functools import wraps

from flask import current_app
from flask import render_template, flash, jsonify
from flask_login import current_user

from app import db
from app.models import Order, User
from app.email import SendEmail


################################################################################
# Utilities
################################################################################

def role_required(roles_list):
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            if current_user.role not in roles_list:
                return render_template('errors/403.html'), 403
            return function(*args, **kwargs)
        return wrapper
    return decorator


def role_forbidden(roles_list):
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            if current_user.role in roles_list:
                return render_template('errors/403.html'), 403
            return function(*args, **kwargs)
        return wrapper
    return decorator


def role_required_ajax(roles_list):
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            if current_user.role not in roles_list:
                return jsonify(
                    {'status': False, 'flash': ['У вас нет соответствующих полномочий.']}
                ), 403
            return function(*args, **kwargs)
        return wrapper
    return decorator


def role_forbidden_ajax(roles_list):
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            if current_user.role in roles_list:
                return jsonify(
                    {'status': False, 'flash': ['У вас нет соответствующих полномочий.']}
                ), 403
            return function(*args, **kwargs)
        return wrapper
    return decorator


def ecwid_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if current_user.hub is None:
            flash('Взаимодействие с ECWID не настроено.')
            return render_template('errors/400.html'), 400
        return function(*args, **kwargs)
    return wrapper


def ecwid_required_ajax(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if current_user.hub is None:
            return jsonify(
                {'status': False, 'flash': ['Взаимодействие с ECWID не настроено.']}
            ), 400
        return function(*args, **kwargs)
    return wrapper


def SendEmailNotification(kind, order, recipients_id=None):
    if recipients_id is None:
        recipients = [
            r.email for r in order.reviewers if getattr(r, f'email_{kind}', False) is True
        ]
    else:
        recipients = [
            r.email for r in order.reviewers if (
                getattr(r, f'email_{kind}', False) is True and r.id in recipients_id
            )
        ]
    if len(recipients) == 0:
        return
    current_app.logger.info(
        '"%s" email about order %s has been sent to %s',
        kind,
        order.id,
        recipients
    )
    if len(recipients) > 0:
        SendEmail(
            f'Уведомление по заявке #{order.id}',
            sender=(current_app.config['MAIL_SENDERNAME'], current_app.config['MAIL_USERNAME']),
            recipients=recipients,
            text_body=render_template(f'email/{kind}.txt', order=order),
            html_body=render_template(f'email/{kind}.html', order=order)
        )


def SendEmail1C(recipients, order, data):
    current_app.logger.info(
        '"export1C" email about order %s has been sent to %s',
        order.id,
        recipients
    )

    if order.site is not None:
        subject = f'{order.site.project.name}. {order.site.name} (pushkind_{order.id})'
    else:
        subject = f'pushkind_{order.id}'

    data = (
        f'pushkind_{order.id}.xlsx',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        data
    )

    SendEmail(
        subject,
        sender=(current_app.config['MAIL_SENDERNAME'], current_app.config['MAIL_USERNAME']),
        recipients=recipients,
        text_body=render_template('email/export1C.txt', order=order),
        html_body=render_template('email/export1C.html', order=order),
        attachments=[data]
    )


def GetNewOrderNumber():
    count = db.session.query(Order).count()
    letter = chr(int(count / 1000) + 97)
    count = count % 1000
    return f'{letter}{count:04d}'
