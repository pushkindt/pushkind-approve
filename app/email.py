from threading import Thread
from flask import current_app
from flask_mail import Message
from app import mail


def SendEmailAsync(app, msg):
	with app.app_context():
		mail.send(msg)


def SendEmail(subject, sender, recipients, text_body, html_body,
			   attachments=None, sync=False):
	current_app.logger.info('Email {} was sent to {}'.format(subject, recipients))
	msg = Message(subject, sender=sender, recipients=recipients)
	msg.body = text_body
	msg.html = html_body
	if attachments:
		for attachment in attachments:
			msg.attach(*attachment)
	if sync:
		mail.send(msg)
	else:
		Thread(target=SendEmailAsync,
			args=(current_app._get_current_object(), msg)).start()