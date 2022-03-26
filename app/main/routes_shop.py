from datetime import datetime, timezone
from urllib.parse import urljoin

from flask import render_template, redirect, url_for, flash, current_app
from flask_login import login_required, current_user

from app import db
from app.main import bp
from app.models import UserRoles, Project, OrderLimit, Category, Product, Ecwid
from app.models import Order, Site, OrderStatus
from app.main.utils import role_required
from app.main.forms import CreateOrderForm
from app.main.utils import SendEmailNotification, GetNewOrderNumber


@bp.route('/shop/')
@login_required
@role_required([UserRoles.initiative, UserRoles.purchaser, UserRoles.admin])
def ShopCategories():
    projects = Project.query
    if current_user.role != UserRoles.admin:
        projects = projects.filter_by(enabled=True)
    projects = projects.filter_by(hub_id=current_user.hub_id)
    projects = projects.order_by(Project.name).all()
    limits = OrderLimit.query.filter_by(hub_id=current_user.hub_id).all()
    categories = Category.query.filter_by(hub_id=current_user.hub_id).all()
    return render_template(
        'shop_categories.html',
        projects=projects,
        limits=limits, 
        categories=categories
    )

@bp.route('/shop/<int:cat_id>', defaults={'vendor_id': None})
@bp.route('/shop/<int:cat_id>/<int:vendor_id>')
@login_required
@role_required([UserRoles.initiative, UserRoles.purchaser, UserRoles.admin])
def ShopProducts(cat_id, vendor_id):
    category = Category.query.filter_by(
        id=cat_id,
        hub_id=current_user.hub_id
    ).first()
    if category is None:
        return redirect(url_for('main.ShopCategories'))
    products = Product.query.filter_by(cat_id=cat_id)
    if vendor_id is not None:
        products = products.filter_by(vendor_id=vendor_id)
    products = products.all()
    vendor_ids = [p.vendor_id for p in products]
    vendors = Ecwid.query.filter(Ecwid.id.in_(vendor_ids)).all()
    return render_template(
        'shop_products.html',
        category=category,
        vendors=vendors,
        products=products,
        vendor_id=vendor_id
    )

@bp.route('/shop/cart', methods=['GET', 'POST'])
@login_required
@role_required([UserRoles.initiative, UserRoles.purchaser, UserRoles.admin])
def ShopCart():
    form = CreateOrderForm()
    if form.submit.data:
        if form.validate_on_submit():
            products = Product.query.filter(
                Product.id.in_(
                    p['product'] for p in form.cart.data
                )
            ).all()
            if len(products) == 0:
                flash('Заявка не может быть пуста.')
                return render_template(
                    'shop_cart.html',
                    form=form,
                    clear_cart=clear_cart
                )
            site = Site.query.filter_by(
                id=form.site_id.data,
                project_id=form.project_id.data
            ).first()
            if site is None:
                flash('Такой площадки не существует.')
                return redirect(url_for('main.ShopCart'))
            order_products = []
            for product in products:
                order_product = {
                    'id': product.id,
                    'sku': product.sku,
                    'price': product.price,
                    'name': product.name,
                    'imageUrl': urljoin(current_app.config['IMAGE_HOSTING_URL'], product.image),
                    'categoryId': product.cat_id,
                    'vendor': product.vendor.name,
                    'category': product.category.name,
                    'selectedOptions': [
                        {
                            'value': product.measurement
                        }
                    ]
                }
                for cart_item in form.cart.data:
                    if cart_item['product'] == product.id:
                        order_product['quantity'] = cart_item['quantity']
                        if product.input_required is True and cart_item['text'] is not None:
                            order_product['selectedOptions'].append(
                                {
                                    'value': cart_item['text']
                                }
                            )
                order_products.append(order_product)
            order_id = GetNewOrderNumber()
            now = datetime.now(tz=timezone.utc)
            categories = Category.query.filter(
                Category.id.in_(
                    p.cat_id for p in products
                )
            ).all()
            order = Order(
                id = order_id,
                initiative_id = current_user.id,
                create_timestamp = int(now.timestamp()),
                site_id = site.id,
                hub_id = current_user.hub_id,
                products = order_products,
                total = sum([p['quantity']*p['price'] for p in order_products]),
                status = OrderStatus.new
            )
            db.session.add(order)
            order.categories = categories
            db.session.commit()
            Order.UpdateOrdersPositions(current_user.hub_id, order_id)
            flash('Заявка успешно создана.')
            return redirect(url_for('main.ShowOrder', order_id=order_id))
        else:
            flash('Что-то пошло не так.')
    return render_template(
        'shop_cart.html',
        form=form
    )
