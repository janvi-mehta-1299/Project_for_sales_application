from flask import Blueprint, render_template, request, redirect, url_for
from common.log import get_logger
from app.controllers import sale
from app.models.sale import Sale
from singletons import db

v = Blueprint('default', __name__)
logger = get_logger('default.view')


@v.route('/')
def index():
    return render_template('pages/add.html.j2')

@v.route('/index')
def home():
    return render_template('pages/index.html.j2')


@v.route('/add-sale', methods=['GET', 'POST'])
def add_sale():
    if request.method == 'POST':
        if request.form:
            try:
                sale.add_sale(
                    total_cost=request.form['total-cost'],
                    commission_rate=request.form['commission-rate'],
                    tax_rate=request.form['tax-rate'],
                    description=request.form['description']
                )
                return redirect(url_for('default.add_sale', msg='created'))
            except Exception as e:
                logger.exception("Error while adding sale")
                db.session.rollback()
                return redirect(url_for('default.add_sale', msg='error'))
        else:
            logger.warning("No form data received")
    msg = request.args.get('msg')
    return render_template('pages/add.html.j2', msg=msg)


@v.route('/list_sales', methods=['GET'])
def list_sales():
    try:
        sales = Sale.query.all()
        sale_list = []
        msg = request.args.get('msg')

        for sale in sales:
            sale.commission_amount = sale.total_price * (sale.commission_rate / 100)
            sale.tax_amount = sale.total_price * (sale.tax_rate / 100)
            sale.final_total_cost = sale.total_price * (
                1 + sale.commission_rate / 100 + sale.tax_rate / 100
            )
            sale_list.append(sale)

        return render_template('pages/list.html.j2', sales=sale_list, msg=msg)

    except Exception as e:
        logger.exception("Error fetching sales")
        return render_template('pages/list.html.j2', sales=[], msg='error')


@v.route('/edit_data/<string:sale_id>', methods=['GET', 'POST'])
def edit_data(sale_id):
    try:
        sale = db.session.get(Sale, sale_id)
        if not sale:
            return redirect(url_for('default.list_sales', msg='not_found'))

        if request.method == 'POST':
            try:
                sale.commission_rate = request.form['commission-rate']
                sale.tax_rate = request.form['tax-rate']
                sale.description = request.form['description']
                db.session.commit()
                return redirect(url_for('default.list_sales', msg='updated'))
            except Exception as e:
                db.session.rollback()
                logger.exception("Failed to update sale")
                return redirect(url_for('default.list_sales', msg='error'))

        return render_template('pages/edit.html.j2', sales=sale)

    except Exception as e:
        logger.exception("Edit operation failed")
        return redirect(url_for('default.list_sales', msg='error'))


@v.route('/delete_data/<string:sale_id>', methods=['GET', 'POST'])
def delete_data(sale_id):
    try:
        sale = db.session.get(Sale, sale_id)
        if not sale:
            return redirect(url_for('default.list_sales', msg='not_found'))

        db.session.delete(sale)
        db.session.commit()
        return redirect(url_for('default.list_sales', msg='deleted'))

    except Exception as e:
        logger.exception("Failed to delete sale")
        db.session.rollback()
        return redirect(url_for('default.list_sales', msg='error'))
