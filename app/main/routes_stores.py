from datetime import datetime, timezone

from flask_login import current_user, login_required
from flask import render_template, redirect, url_for, flash

from app import db
from app.main import bp
from app.models import UserRoles, Vendor, User
from app.main.forms import AddStoreForm
from app.main.utils import role_required, role_forbidden


################################################################################
# Stores page
################################################################################

@bp.route('/stores/', methods=['GET', 'POST'])
@login_required
@role_forbidden([UserRoles.default, UserRoles.vendor])
def ShowStores():
    store_form = AddStoreForm()
    stores = Vendor.query.filter(Vendor.hub_id == current_user.hub_id).all()
    if len(stores) == 0:
        flash('Ни один поставщик не зарегистрован в системе.')
    return render_template('stores.html', store_form=store_form, stores=stores)


@bp.route('/stores/add/', methods=['POST'])
@login_required
@role_required([UserRoles.admin])
def AddStore():
    form = AddStoreForm()
    if form.validate_on_submit():
        store_name = form.name.data.strip()
        store_email = form.email.data.strip().lower()
        vendor_admin = User.query.filter_by(email=store_email).first()
        if vendor_admin:
            flash('Невозможно создать поставщика, так как электронный адрес занят.')
            return redirect(url_for('main.ShowStores'))
        vendor_admin = User(
            email=store_email,
            name=store_name,
            role=UserRoles.vendor,
            hub_id=current_user.hub_id
        )
        vendor_admin.set_password(form.password.data)
        vendor_admin.registered = datetime.now(tz=timezone.utc)
        db.session.add(vendor_admin)
        db.session.commit()
        store = Vendor(
            hub_id=current_user.hub_id,
            name=store_name,
            email=store_email,
            admin_id = vendor_admin.id
        )
        db.session.add(store)
        db.session.commit()
        flash('Магазин успешно добавлен.')
    else:
        errors = (
            form.name.errors +
            form.email.errors +
            form.password.errors
        )
        for error in errors:
            flash(error)
    return redirect(url_for('main.ShowStores'))


@bp.route('/stores/remove/<int:store_id>')
@login_required
@role_required([UserRoles.admin])
def RemoveStore(store_id):
    store = Vendor.query.filter(
        Vendor.id == store_id,
        Vendor.hub_id == current_user.hub_id
    ).first()
    if store is not None:
        vendor_admin = store.admin
        db.session.delete(store)
        if vendor_admin is not None:
            db.session.delete(vendor_admin)
        db.session.commit()
        flash('Поставщик успешно удалён.')
    else:
        flash('Этот поставщик не зарегистрован в системе.')
    return redirect(url_for('main.ShowStores'))


@bp.route('/stores/activate/<int:store_id>')
@login_required
@role_required([UserRoles.admin])
def ActivateStore(store_id):
    store = Vendor.query.filter(
        Vendor.id == store_id,
        Vendor.hub_id == current_user.hub_id
    ).first()
    if store is not None:
        store.enabled = not store.enabled
        db.session.commit()
        flash('Поставщик успешно изменён.')
    else:
        flash('Этот поставщик не зарегистрован в системе.')
    return redirect(url_for('main.ShowStores'))