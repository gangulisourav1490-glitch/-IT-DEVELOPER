from backend.models import db

class Product(db.Model):
    __tablename__ = "product"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    sku = db.Column(db.String(100))
    category = db.Column(db.String(100))
    stock = db.Column(db.Integer)
    price = db.Column(db.Float)
    min_stock = db.Column(db.Integer, default=5) 
   