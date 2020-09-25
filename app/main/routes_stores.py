from app import db
from flask_login import current_user, login_required
from app.main import bp
from app.models import User, UserRoles, Ecwid
from flask import render_template, redirect, url_for, flash
from app.main.forms import AddStoreForm
from app.ecwid import EcwidAPIException
import subprocess
from app.main.utils import role_required, ecwid_required, role_forbidden

'''
################################################################################
Stores page
################################################################################
'''
@bp.route('/stores/', methods=['GET', 'POST'])
@login_required
@role_forbidden([UserRoles.default])
@ecwid_required
def ShowStores():
	store_form = AddStoreForm()
	if current_user.role == UserRoles.admin:
		if store_form.validate_on_submit():
			try:
				store_name = store_form.name.data.strip()
				store_email = store_form.email.data.strip().lower()
				store_id = current_user.hub.EcwidCreateStore(name = store_name, email = store_email, password = store_form.password.data, plan = store_form.plan.data,
																defaultlanguage='ru')
				store = Ecwid(store_id = store_id, ecwid_id = current_user.ecwid_id, partners_key = current_user.hub.partners_key,
								client_id = current_user.hub.client_id, client_secret = current_user.hub.client_secret)
				db.session.add(store)
				store.EcwidGetStoreToken()
				store.EcwidUpdateStoreProfile({'settings':{'storeName':store_name}, 'company':{'companyName':store_name, 'city':'Москва', 'countryCode':'RU'}})
				db.session.commit()
				flash('Магазин успешно добавлен.')
			except EcwidAPIException as e:
				db.session.rollback()
				flash('Ошибка API или магазин уже используется.')
				flash('Возможно неверные настройки?')
	vendors = Ecwid.query.filter(Ecwid.ecwid_id == current_user.ecwid_id).all()
	stores = list()
	for vendor in vendors:
		try:
			stores.append(vendor.EcwidGetStoreProfile())
		except EcwidAPIException as e:
			flash('Ошибка API: {}'.format(e))
	if len(stores) == 0:
		flash('Ни один поставщик не зарегистрован в системе.')
	return render_template('stores.html', store_form = store_form, stores = stores)
	
	
@bp.route('/withdraw/<int:store_id>')
@login_required
@role_required([UserRoles.admin])
@ecwid_required
def WithdrawStore(store_id):
	store = Ecwid.query.filter(Ecwid.store_id == store_id, Ecwid.ecwid_id == current_user.ecwid_id).first()
	if store:
		try:
			store.EcwidDeleteStore()
		except EcwidAPIException as e:
			flash('Ошибка удаления магазина: {}'.format(e))
		
		try:
			json = current_user.hub.EcwidGetStoreProducts(keyword = store.store_id)
			products = json.get('items', [])
		except EcwidAPIException as e:
			flash('Ошибка удаления товаров: {}'.format(e))
			products = []
			
		for product in products:
			try:
				current_user.hub.EcwidDeleteStoreProduct(product['id'])
			except EcwidAPIException as e:
				flash('Ошибка удаления товаров: {}'.format(e))
				continue
		db.session.delete(store)
		db.session.commit()
		flash('Поставщик успешно удалён.')
	else:	
		flash('Этот поставщик не зарегистрован в системе.')
	return redirect(url_for('main.ShowStores'))
	
@bp.route('/sync/', defaults={'store_id': None})
@bp.route('/sync/<int:store_id>')
@login_required
@role_required([UserRoles.admin])
@ecwid_required
def SyncStores(store_id):
	if not store_id:
		args = ("c/ecwid-api", str(current_user.ecwid_id))
	else:
		args = ("c/ecwid-api", str(current_user.ecwid_id), str(store_id))
	popen = subprocess.Popen(args, stderr=subprocess.PIPE)
	popen.wait()
	output = popen.stderr.read()
	if output and len(output) > 0:
		for s in output.decode('utf-8').strip().split('\n'):
			flash(s)
	else:
		flash('Синхронизация успешно завершена.')
	return redirect(url_for('main.ShowStores'))