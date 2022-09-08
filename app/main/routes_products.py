import io
from zipfile import ZipFile
from pathlib import Path

from flask import redirect, render_template, request, url_for, flash, current_app
from flask import send_file
from flask_login import current_user, login_required
import pandas as pd


from app import db
from app.main import bp
from app.models import Product, UserRoles, Product, Vendor, Category
from app.main.utils import role_forbidden
from app.main.forms import UploadProductsForm, UploadImagesForm
from app.main.forms import UploadProductImageForm


################################################################################
# Vendor products page
################################################################################

@bp.route('/products/', methods=['GET', 'POST'])
@bp.route('/products/show', methods=['GET', 'POST'])
@login_required
@role_forbidden([UserRoles.default, UserRoles.initiative, UserRoles.supervisor])
def ShowProducts():
    products_form = UploadProductsForm()
    images_form = UploadImagesForm()
    product_image_form = UploadProductImageForm()
    vendors = Vendor.query.filter_by(hub_id = current_user.hub_id)
    if current_user.role == UserRoles.vendor:
        vendors = vendors.filter_by(email=current_user.email)
    vendor_id = request.args.get('vendor_id', type=int)
    if vendor_id is None:
        vendor = vendors.first()
    else:
        vendor = vendors.filter_by(id=vendor_id).first()
    vendors = vendors.all()
    categories = Category.query.filter_by(hub_id=current_user.hub_id).all()
    return render_template(
        'products.html',
        vendors=vendors,
        vendor=vendor,
        categories=categories,
        products_form=products_form,
        images_form=images_form,
        product_image_form=product_image_form,
    )


@bp.route('/products/upload', methods=['GET', 'POST'])
@login_required
@role_forbidden([UserRoles.default, UserRoles.initiative, UserRoles.supervisor])
def UploadProducts():
    form = UploadProductsForm()
    if current_user.role == UserRoles.vendor:
        vendor = Vendor.query.filter_by(email=current_user.email).first()
    else:
        vendor_id = request.args.get('vendor_id', type=int)
        vendor = Vendor.query.filter_by(id=vendor_id).first()
    if vendor is None:
        flash('Такой поставщик не найден.')
        return redirect(url_for('main.ShowProducts'))

    if form.validate_on_submit():
        df = pd.read_excel(
            form.products.data,
            engine='openpyxl'
        )
        df.columns = df.columns.str.lower()
        df.drop(
            df.columns.difference([
                'name',
                'sku',
                'price',
                'measurement',
                'category',
                'description'
            ]),
            axis=1,
            inplace=True
        )
        df = df.astype(
            dtype = {
                'name': str,
                'sku': str,
                'price': float,
                'measurement': str,
                'description': str,
                'category': str
            }
        )
        df['vendor_id'] = vendor.id
        categories = Category.query.filter_by(hub_id=current_user.hub_id).all()
        categories = {c.name.lower():c.id for c in categories}
        df['cat_id'] = df['category'].apply(lambda x: categories.get(x.lower()))
        df.drop(['category'], axis=1, inplace=True)
        df.dropna(subset=['cat_id', 'name', 'sku', 'price', 'measurement'], inplace=True)
        static_path = Path(f'app/static/upload/vendor{vendor.id}')
        static_path.mkdir(parents=True, exist_ok=True)
        image_list = {
            f.stem:url_for('static', filename=Path(*static_path.parts[2:]) / f.name)
            for f in static_path.glob('*') if not f.is_dir()
        }

        df['image'] = df['sku'].apply(lambda x: image_list.get(x))

        df['name'] = df['name'].str.slice(0,128)
        df['sku'] = df['sku'].str.slice(0,128)
        df['measurement'] = df['measurement'].str.slice(0,128)
        df['description'] = df['description'].str.slice(0,512)

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
@role_forbidden([UserRoles.default, UserRoles.initiative, UserRoles.supervisor])
def UploadImages():
    form = UploadImagesForm()
    if current_user.role == UserRoles.vendor:
        vendor = Vendor.query.filter_by(email=current_user.email).first()
    else:
        vendor_id = request.args.get('vendor_id', type=int)
        vendor = Vendor.query.filter_by(id=vendor_id).first()
    if vendor is None:
        flash('Такой поставщик не найден.')
        return redirect(url_for('main.ShowProducts'))
    if form.validate_on_submit():
        products = Product.query.filter_by(vendor_id=vendor.id).all()
        products = [p.sku for p in products]
        with ZipFile(form.images.data, 'r') as zip_file:
            for zip_info in zip_file.infolist():
                if zip_info.is_dir() or zip_info.file_size > current_app.config['MAX_ZIP_FILE_SIZE']:
                    continue
                file_name = Path(zip_info.filename)
                sku = file_name.stem
                print(sku)
                if sku not in products:
                    continue
                zip_info.filename = sku + file_name.suffix
                static_path = Path(f'app/static/upload/vendor{vendor.id}')
                static_path.mkdir(parents=True, exist_ok=True)
                zip_file.extract(zip_info, static_path)
                static_path = static_path / zip_info.filename
                db.session.query(Product).filter_by(vendor_id=vendor.id, sku=sku).update(
                    {
                        'image': url_for('static', filename=Path(*static_path.parts[2:]))
                    }
                )
                db.session.commit()
        flash('Изображения товаров успешно загружены.')
    else:
        for error in form.images.errors:
            flash(error)
    return redirect(url_for('main.ShowProducts', vendor_id=vendor.id))


@bp.route('/products/download', methods=['GET', 'POST'])
@login_required
@role_forbidden([UserRoles.default, UserRoles.initiative, UserRoles.supervisor])
def DownloadProducts():
    if current_user.role == UserRoles.vendor:
        vendor = Vendor.query.filter_by(email=current_user.email).first()
    else:
        vendor_id = request.args.get('vendor_id', type=int)
        vendor = Vendor.query.filter_by(id=vendor_id).first()

    if vendor is None:
        flash('Такой поставщик не найден.')
        return redirect(url_for('main.ShowProducts'))

    products = Product.query.filter_by(vendor_id=vendor.id)
    df = pd.read_sql(products.statement, products.session.bind)
    categories = Category.query.filter_by(hub_id=current_user.hub_id).all()
    categories = {c.id:c.name for c in categories}
    df['category'] = df['cat_id'].apply(lambda x: categories.get(x))
    df.drop(['id', 'image', 'vendor_id', 'cat_id'], axis='columns', inplace=True)
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        download_name='products.xlsx'
    )


@bp.route('/products/<int:id>/upload/image', methods=['GET', 'POST'])
@login_required
@role_forbidden([UserRoles.default, UserRoles.initiative, UserRoles.supervisor])
def UploadProductImage(id):
    if current_user.role == UserRoles.vendor:
        vendor = Vendor.query.filter_by(email=current_user.email).first()
    else:
        vendor_id = request.args.get('vendor_id', type=int)
        vendor = Vendor.query.filter_by(id=vendor_id).first()
    if vendor is None:
        flash('Такой поставщик не найден.')
        return redirect(url_for('main.ShowProducts'))

    product = Product.query.filter_by(id=id, vendor_id=vendor.id).first()
    if product is None:
        flash('Такой товар не найден.')
        return redirect(url_for('main.ShowProducts'))

    form = UploadProductImageForm()
    if form.validate_on_submit():
        f = form.image.data
        file_name = Path(f.filename)
        file_name = Path(str(product.sku) + file_name.suffix)
        static_path = Path(f'app/static/upload/vendor{vendor.id}')
        static_path.mkdir(parents=True, exist_ok=True)
        full_path = static_path / file_name
        f.save(full_path)
        product.image = url_for('static', filename=(Path(*static_path.parts[2:])))
        db.session.commit()
        flash('Изображение товара успешно загружено.')
    else:
        for error in form.image.errors:
            flash(error)
    return redirect(url_for('main.ShowProducts', vendor_id=vendor.id))
