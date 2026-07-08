from backend.models import db
from backend.models.product import Product
from backend.models.supplier import Supplier
from datetime import datetime

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'))

    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float)

    date = db.Column(db.DateTime, default=datetime.utcnow)