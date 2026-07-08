from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .user import User
from .product import Product
from .supplier import Supplier
from .sale import Sale
from .purchase import Purchase