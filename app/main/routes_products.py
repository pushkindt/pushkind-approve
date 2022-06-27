import os
from zipfile import ZipFile

from flask import redirect, render_template, request, url_for, flash, current_app
from flask_login import current_user, login_required
import pandas as pd

from app import db
from app.main import bp
from app.models import Product, UserRoles, Product, Vendor, Category
from app.main.utils import role_required
from app.main.forms import UploadProductsForm, UploadImagesForm


################################################################################
# Vendor products page
################################################################################

@bp.route('/products/', methods=['GET', 'POST'])
@bp.route('/products/show', methods=['GET', 'POST'])
@login_required
@role_required([UserRoles.admin, UserRoles.vendor])
def ShowProducts():
    products_form = UploadProductsForm()
    images_form = UploadImagesForm()
    vendors = Vendor.query.filter_by(hub_id = current_user.hub_id)
    if current_user.role == UserRoles.vendor:
        vendors = vendors.filter_by(admin_id=current_user.id)
    vendor_id = request.args.get('vendor_id', type=int)
    if vendor_id is None:
        vendor = vendors.first()
    else:
        vendor = vendors.filter_by(id=vendor_id).first()
    vendors = vendors.all()
    products = Product.query.filter(Product.id.in_(v.id for v in vendors)).all()
    return render_template(
        'products.html',
        vendors=vendors,
        vendor=vendor,
        products=products,
        products_form=products_form,
        images_form=images_form
    )

@bp.route('/products/upload', methods=['GET', 'POST'])
@login_required
@role_required([UserRoles.admin, UserRoles.vendor])
def UploadProducts():
    form = UploadProductsForm()
    if current_user.role == UserRoles.admin:
        vendor_id = request.args.get('vendor_id', type=int)
        vendor = Vendor.query.filter_by(id=vendor_id).first()
    elif current_user.role == UserRoles.vendor:
        vendor = Vendor.query.filter_by(admin_id=current_user.id).first()
    if vendor is None:
        flash('Такой поставщик не найден.')
    else:
        if form.validate_on_submit():
            df = pd.read_excel(form.products.data, engine='openpyxl')
            df.columns= df.columns.str.lower()
            df['vendor_id'] = vendor.id
            categories = Category.query.filter_by(hub_id=current_user.hub_id).all()
            categories = {c.name.lower():c.id for c in categories}
            df['cat_id'] = df['category'].apply(lambda x: categories.get(x.lower()))
            df.drop(df.columns.difference(['name','sku', 'price', 'measurement', 'cat_id', 'vendor_id', 'description']), axis=1, inplace=True)
            df.dropna(subset=['cat_id'], inplace=True)
            Product.query.filter_by(vendor_id=vendor.id).delete()
            db.session.commit()
            df.to_sql(name = 'product', con = db.engine, if_exists = 'append', index = False)
            db.session.commit()
            flash('Список товаров успешно обновлён.')
        else:
            for error in form.products.errors:
                flash(error)
    return redirect(url_for('main.ShowProducts', vendor_id=vendor.id))

@bp.route('/products/upload/images', methods=['GET', 'POST'])
@login_required
@role_required([UserRoles.admin, UserRoles.vendor])
def UploadImages():
    form = UploadImagesForm()
    if current_user.role == UserRoles.admin:
        vendor_id = request.args.get('vendor_id', type=int)
        vendor = Vendor.query.filter_by(id=vendor_id).first()
    elif current_user.role == UserRoles.vendor:
        vendor = Vendor.query.filter_by(admin_id=current_user.id).first()
    if vendor is None:
        flash('Такой поставщик не найден.')
    else:
        if form.validate_on_submit():
            products = Product.query.filter_by(vendor_id=vendor.id).all()
            products = [p.sku for p in products]
            with ZipFile(form.images.data, 'r') as zip_file:
                for zip_info in zip_file.infolist():
                    if zip_info.is_dir() or zip_info.file_size > current_app.config['MAX_ZIP_FILE_SIZE']:
                        continue
                    sku, file_ext = os.path.splitext(os.path.basename(zip_info.filename))
                    if sku not in products:
                        continue
                    zip_info.filename = sku + file_ext
                    full_path = os.path.join(
                        'app',
                        'static',
                        'upload',
                        f'vendor{vendor.id}'
                    )
                    zip_file.extract(zip_info, full_path)
                    db.session.query(Product).filter_by(vendor_id=vendor.id, sku=sku).update(
                        {
                            'image': url_for('static', filename=os.path.join(
                                'upload',
                                f'vendor{vendor.id}',
                                zip_info.filename
                            ))
                        }
                    )
                    db.session.commit()
            flash('Изображения товаров успешно загружены.')
        else:
            for error in form.images.errors:
                flash(error)
    return redirect(url_for('main.ShowProducts', vendor_id=vendor.id))