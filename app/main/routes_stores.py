import subprocess

from flask_login import current_user, login_required
from flask import render_template, redirect, url_for, flash, jsonify, request, current_app

from app import db
from app.main import bp
from app.models import UserRoles, Ecwid, Order
from app.main.forms import AddStoreForm
from app.ecwid import EcwidAPIException
from app.main.utils import role_required, ecwid_required, role_forbidden, role_forbidden_ajax
from app.main.utils import ecwid_required_ajax, SendEmailNotification

################################################################################
# Stores page
################################################################################

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
                store_id = current_user.hub.CreateStore(
                    name=store_name,
                    email=store_email,
                    password=store_form.password.data,
                    plan=store_form.plan.data,
                    defaultlanguage='ru'
                )
                store = Ecwid(
                    id=store_id,
                    hub_id=current_user.hub_id,
                    partners_key=current_user.hub.partners_key,
                    client_id=current_user.hub.client_id,
                    client_secret=current_user.hub.client_secret,
                    name=store_name,
                    email=store_email
                )
                db.session.add(store)
                store.GetStoreToken()
                store.UpdateStoreProfile(
                    {
                        'settings': {'storeName': store_name},
                        'company': {
                            'companyName': store_name,
                            'city': 'Москва',
                            'countryCode': 'RU'
                        }
                    }
                )
                db.session.commit()
                flash('Магазин успешно добавлен.')
            except EcwidAPIException:
                db.session.rollback()
                flash('Ошибка API или магазин уже используется.')
                flash('Возможно неверные настройки?')
            return redirect(url_for('main.ShowStores'))

    stores = Ecwid.query.filter(Ecwid.hub_id == current_user.hub_id).all()
    if len(stores) == 0:
        flash('Ни один поставщик не зарегистрован в системе.')
    return render_template('stores.html', store_form=store_form, stores=stores)


@bp.route('/stores/remove/<int:store_id>')
@login_required
@role_required([UserRoles.admin])
@ecwid_required
def RemoveStore(store_id):
    store = Ecwid.query.filter(
        Ecwid.id == store_id, Ecwid.hub_id == current_user.hub_id).first()
    if store is not None:
        try:
            store.DeleteStore()
        except EcwidAPIException as e:
            flash(f'Ошибка удаления магазина: {e}')

        try:
            json = current_user.hub.GetStoreProducts(keyword=store.store_id)
            products = json.get('items', [])
        except EcwidAPIException as e:
            flash(f'Ошибка удаления товаров: {e}')
            products = []

        for product in products:
            try:
                current_user.hub.DeleteStoreProduct(product['id'])
            except EcwidAPIException as e:
                flash(f'Ошибка удаления товаров: {e}')
                continue
        db.session.delete(store)
        db.session.commit()
        flash('Поставщик успешно удалён.')
    else:
        flash('Этот поставщик не зарегистрован в системе.')
    return redirect(url_for('main.ShowStores'))


@bp.route('/stores/sync/products/', defaults={'store_id': None})
@bp.route('/stores/sync/products/<int:store_id>')
@login_required
@role_required([UserRoles.admin, UserRoles.purchaser])
@ecwid_required
def SyncStoreProducts(store_id):
    if store_id is None:
        args = ('c/bin/ecwid-api', 'products', str(current_user.hub_id))
    else:
        args = ('c/bin/ecwid-api', 'products',
                str(current_user.hub_id), '-s', str(store_id))
    popen = subprocess.Popen(args, stderr=subprocess.PIPE)
    popen.wait()
    if popen.returncode != 0:
        process_output = popen.stderr.read()
        if process_output is not None and len(process_output) > 0:
            for s in process_output.decode('utf-8').strip().split('\n'):
                current_app.logger.error(s)
        flash('Синхронизация завершена с ошибками.')
    else:
        flash('Синхронизация успешно завершена.')
    return redirect(url_for('main.ShowStores'))


@bp.route('/stores/sync/orders/')
@login_required
@role_forbidden_ajax([UserRoles.default, UserRoles.supervisor, UserRoles.validator])
@ecwid_required_ajax
def SyncStoreOrders():
    order_id = request.args.get('id', default=None, type=str)
    if order_id is None:
        args = ('c/bin/ecwid-api', 'orders', str(current_user.hub_id))
    else:
        args = ('c/bin/ecwid-api', 'orders',
                str(current_user.hub_id), '-o', order_id)
    popen = subprocess.Popen(args, stderr=subprocess.PIPE)
    popen.wait()
    messages = []
    if popen.returncode != 0:
        process_output = popen.stderr.read()
        if process_output is not None and len(process_output) > 0:
            for s in process_output.decode('utf-8').strip().split('\n'):
                current_app.logger.error(s)
        messages.append('Синхронизация завершена с ошибками.')
        status = False
    else:
        messages.append('Синхронизация успешно завершена.')
        status = True
    if order_id is not None:
        order = Order.query.filter_by(id = order_id).first()
        if order is not None:
            SendEmailNotification('new', order)
    return jsonify({'status': status, 'flash': messages})
