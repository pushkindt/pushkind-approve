import datetime as dt

import markdown
from flask import Response, abort, current_app, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from approve.email import SendEmail
from approve.extensions import db
from approve.main.forms import SendMessageForm
from approve.main.routes import bp
from approve.main.utils import role_forbidden
from approve.models import Email, EmailRecipient, User, UserRoles
from approve.utils import flash_errors


def get_email_recipients(users: list[User]):
    recipients = []
    for role in UserRoles:
        if role == UserRoles.default:
            continue
        recipients.append((role.value, f"Роль: {role}"))
    for user in users:
        if user.role == UserRoles.default:
            continue
        recipients.append((user.email, user.name))
    return recipients


@bp.route("/messages", methods=["GET", "POST"])
@login_required
@role_forbidden([UserRoles.default])
def send_message():
    form = SendMessageForm()
    form.recipients.choices = get_email_recipients(current_user.hub.users)
    if form.validate_on_submit():
        recipients = []
        for recipient in form.recipients.data:
            if "@" in recipient:
                user = User.query.filter_by(email=recipient).first()
                if user:
                    recipients.append(user.email)
            else:
                role = UserRoles(int(recipient))
                users = User.query.filter_by(role=role, hub_id=current_user.hub_id).all()
                for user in users:
                    recipients.append(user.email)

        email_message = markdown.markdown(form.message.data)
        email = Email(user_id=current_user.id, message=email_message, timestamp=dt.datetime.now(dt.timezone.utc))
        db.session.add(email)
        db.session.commit()
        for recipient in set(recipients):
            email_recipient = EmailRecipient(email_id=email.id, address=recipient)
            db.session.add(email_recipient)
            tracking_img = (
                '<img height="1" width="1" src="'
                + url_for("main.track_message", email_id=email.id, recipient=recipient, _external=True)
                + '">'
            )
            SendEmail(
                subject=current_app.config["title"],
                sender=(current_user.name, current_app.config["mail_username"]),
                recipients=[recipient],
                text_body=form.message.data,
                html_body=email_message + tracking_img,
            )
        db.session.commit()
        flash("Сообщение отправлено.", "success")
        return redirect(url_for("main.send_message"))

    flash_errors(form)
    user_emails = Email.query.filter_by(user_id=current_user.id).order_by(Email.timestamp.desc()).all()
    return render_template("main/messages/messages.html", form=form, emails=user_emails)


@bp.route("/message/track/<int:email_id>/<recipient>", methods=["GET"])
def track_message(email_id: int, recipient: str):
    recipient = EmailRecipient.query.filter_by(email_id=email_id, address=recipient).first()
    if recipient:
        recipient.opened = True
        db.session.commit()
    response = '<?xml version="1.0" encoding="UTF-8"?><svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"/>'
    return Response(response, mimetype="image/svg+xml")
