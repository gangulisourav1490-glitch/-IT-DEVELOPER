from backend.models import db
from datetime import datetime


class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    product_name = db.Column(db.String(100))

    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)