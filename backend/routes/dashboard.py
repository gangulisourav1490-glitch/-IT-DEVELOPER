from flask import Blueprint, jsonify
from backend.models.product import Product

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/api/stock-summary')
def stock_summary():

    products = Product.query.all()

    in_stock = 0
    low_stock = 0
    out_stock = 0

    for p in products:
        if p.stock <= 0:
            out_stock += 1
        elif p.stock < 5:
            low_stock += 1
        else:
            in_stock += 1

    return jsonify({
        "in_stock": in_stock,
        "low_stock": low_stock,
        "out_stock": out_stock
    })