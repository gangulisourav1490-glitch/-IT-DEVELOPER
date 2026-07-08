from flask import Blueprint, request, jsonify, session, render_template, redirect
from backend.models import db
from backend.models.product import Product
from backend.models.sale import Sale
from backend.models.user import User
from werkzeug.security import generate_password_hash
from functools import wraps
from backend.models.supplier import Supplier
from sqlalchemy import func
import csv
import io
from flask import Response, send_file
from reportlab.pdfgen import canvas
from backend.models.purchase import Purchase


employee_bp = Blueprint("employee_bp", __name__, url_prefix="/api")


# =========================
# 🔐 AUTH MIDDLEWARE
# =========================
def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect("/login")
        return func(*args, **kwargs)
    return wrapper


def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if session.get("role") != "admin":
            return render_template("403.html"), 403
        return func(*args, **kwargs)
    return wrapper


# =========================
# 📦 PRODUCTS
# =========================
@employee_bp.route("/get_products", methods=["GET"])
@login_required
def get_products():
    products = Product.query.all()

    return jsonify([
        {
            "id": p.id,
            "name": p.name,
            "sku": p.sku,
            "category": p.category,
            "stock": p.stock,
            "price": p.price,
            "is_low": p.stock < 5
        } for p in products
    ])


@employee_bp.route("/add_product", methods=["POST"])
@login_required
@admin_required
def add_product():
    data = request.get_json()

    if not data.get("name") or not data.get("sku"):
        return jsonify({"error": "Name and SKU required"}), 400

    try:
        stock = int(data.get("stock"))
        price = float(data.get("price"))
    except:
        return jsonify({"error": "Invalid stock or price"}), 400

    product = Product(
        name=data.get("name"),
        sku=data.get("sku"),
        category=data.get("category"),
        stock=stock,
        price=price
    )

    db.session.add(product)
    db.session.commit()

    return jsonify({"message": "Product added"})


@employee_bp.route("/delete_product/<int:id>", methods=["DELETE"])
@login_required
@admin_required
def delete_product(id):
    product = db.session.get(Product, id)

    if not product:
        return jsonify({"error": "Not found"}), 404

    db.session.delete(product)
    db.session.commit()

    return jsonify({"message": "Product deleted"})


@employee_bp.route("/update_product/<int:id>", methods=["PUT"])
@login_required
@admin_required
def update_product(id):
    product = db.session.get(Product, id)

    if not product:
        return jsonify({"error": "Not found"}), 404

    data = request.get_json()

    try:
        product.name = data.get("name")
        product.sku = data.get("sku")
        product.category = data.get("category")
        product.stock = int(data.get("stock"))
        product.price = float(data.get("price"))
    except:
        return jsonify({"error": "Invalid data"}), 400

    db.session.commit()

    return jsonify({"message": "Product updated"})


# =========================
# 💰 SALES
# =========================
@employee_bp.route("/add_sale", methods=["POST"])
@login_required
def add_sale():
    data = request.get_json()

    product = db.session.get(Product, data.get("product_id"))

    if not product:
        return jsonify({"error": "Product not found"}), 404

    try:
        qty = int(data.get("quantity"))
    except:
        return jsonify({"error": "Invalid quantity"}), 400

    if qty <= 0:
        return jsonify({"error": "Invalid quantity"}), 400

    if product.stock < qty:
        return jsonify({"error": "Not enough stock"}), 400

    product.stock -= qty

    sale = Sale(
        product_id=product.id,
        product_name=product.name,
        quantity=qty,
        total_price=qty * product.price
    )

    db.session.add(sale)
    db.session.commit()

    return jsonify({"message": "Sale successful"})


@employee_bp.route("/get_sales", methods=["GET"])
@login_required
def get_sales():
    sales = Sale.query.order_by(Sale.id.desc()).all()

    return jsonify([
        {
            "id": s.id,
            "product_name": s.product_name,
            "quantity": s.quantity,
            "total_price": s.total_price,
            "date": s.created_at.strftime("%Y-%m-%d") if s.created_at else ""
        }
        for s in sales
    ])


# =========================
# 📊 STATS
# =========================
@employee_bp.route("/stats", methods=["GET"])
@login_required
def get_stats():
    total_products = Product.query.count()
    total_sales = db.session.query(db.func.sum(Sale.total_price)).scalar() or 0
    low_stock = Product.query.filter(Product.stock < 5).count()

    return jsonify({
        "total_products": total_products,
        "total_sales": total_sales,
        "low_stock": low_stock
    })


# =========================
# 👤 USERS
# =========================
@employee_bp.route("/users", methods=["GET"])
@login_required
@admin_required
def get_users():
    users = User.query.all()

    return jsonify([
        {
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "role": u.role
        }
        for u in users
    ])


@employee_bp.route("/create_user", methods=["POST"])
@login_required
@admin_required
def create_user():
    data = request.get_json()

    if not data.get("name") or not data.get("email") or not data.get("password"):
        return jsonify({"error": "All fields required"}), 400

    if User.query.filter_by(email=data.get("email")).first():
        return jsonify({"error": "Email already exists"}), 400

    role = data.get("role")
    if role not in ["admin", "user"]:
        role = "user"

    user = User(
        name=data.get("name"),
        email=data.get("email"),
        password=generate_password_hash(data.get("password")),
        role=role
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User created"})


@employee_bp.route("/delete_user/<int:id>", methods=["DELETE"])
@login_required
@admin_required
def delete_user(id):
    user = db.session.get(User, id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    if user.id == session.get("user_id"):
        return jsonify({"error": "You cannot delete yourself"}), 400

    db.session.delete(user)
    db.session.commit()

    return jsonify({"message": "User deleted"})


# =========================
# 🖥 PAGES
# =========================
@employee_bp.route("/products_page")
@login_required
def products_page():
    return render_template("products.html")


@employee_bp.route("/sales_page")
@login_required
def sales_page():
    return render_template("sales.html")


@employee_bp.route("/product_list_page")
@login_required
def product_list_page():
    return render_template("product_list.html")


@employee_bp.route("/users_page")
@login_required
@admin_required
def users_page():
    return render_template("users.html")

@employee_bp.route("/get_suppliers", methods=["GET"])
@login_required
@admin_required
def get_suppliers():
    suppliers = Supplier.query.all()

    return jsonify([
        {
            "id": s.id,
            "name": s.name,
            "phone": s.phone,
            "email": s.email,
            "address": s.address
        } for s in suppliers
    ])

@employee_bp.route("/create_supplier", methods=["POST"])
@login_required
@admin_required
def create_supplier():
    data = request.get_json()

    if not data.get("name"):
        return jsonify({"error": "Name required"}), 400

    supplier = Supplier(
        name=data.get("name"),
        phone=data.get("phone"),
        email=data.get("email"),
        address=data.get("address")
    )

    db.session.add(supplier)
    db.session.commit()

    return jsonify({"message": "Supplier created"})

@employee_bp.route("/delete_supplier/<int:id>", methods=["DELETE"])
@login_required
@admin_required
def delete_supplier(id):
    supplier = db.session.get(Supplier, id)

    if not supplier:
        return jsonify({"error": "Not found"}), 404

    db.session.delete(supplier)
    db.session.commit()

    return jsonify({"message": "Supplier deleted"})

@employee_bp.route("/suppliers_page")
@login_required
@admin_required
def suppliers_page():
    return render_template("suppliers.html")

@employee_bp.route("/reports", methods=["GET"])
@login_required
@admin_required
def get_reports():

    total_sales = db.session.query(
        func.sum(Sale.total_price)
    ).scalar() or 0

    total_orders = Sale.query.count()

    total_products = Product.query.count()

    low_stock = Product.query.filter(
        Product.stock < 5
    ).count()


    return jsonify({
        "total_sales": total_sales,
        "total_orders": total_orders,
        "total_products": total_products,
        "low_stock": low_stock
    })

@employee_bp.route("/reports/daily", methods=["GET"])
@login_required
@admin_required
def daily_report():

    data = db.session.query(
        func.date(Sale.created_at),
        func.sum(Sale.total_price)
    ).group_by(func.date(Sale.created_at)).all()

    return jsonify([
        {
            "date": str(row[0]),
            "total": row[1]
        }
        for row in data
    ])

@employee_bp.route("/reports/top-products", methods=["GET"])
@login_required
@admin_required
def top_products():

    data = db.session.query(
        Sale.product_name,
        func.sum(Sale.quantity).label("total_qty")
    ).group_by(Sale.product_name)\
     .order_by(func.sum(Sale.quantity).desc())\
     .limit(5).all()

    return jsonify([
        {
            "product": row[0],
            "quantity": row[1]
        }
        for row in data
    ])

@employee_bp.route("/reports_page")
@login_required
@admin_required
def reports_page():
    return render_template("reports.html")

@employee_bp.route("/reports/low-stock", methods=["GET"])
@login_required
@admin_required
def low_stock_report():

    products = Product.query.filter(Product.stock < 5).all()

    return jsonify([
        {
            "id": p.id,
            "name": p.name,
            "sku": p.sku,
            "stock": p.stock,
            "price": p.price,
            "category": p.category
        }
        for p in products
    ])

@employee_bp.route("/reports/export/csv", methods=["GET"])
@login_required
@admin_required
def export_csv():

    sales = Sale.query.all()

    def generate():
        yield "ID,Product,Quantity,Total,Date\n"

        for s in sales:
            yield f"{s.id},{s.product_name},{s.quantity},{s.total_price},{s.created_at}\n"

    return Response(
        generate(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=sales_report.csv"}
    )

@employee_bp.route("/reports/export/pdf", methods=["GET"])
@login_required
@admin_required
def export_pdf():

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)

    sales = Sale.query.all()

    y = 800

    p.setFont("Helvetica-Bold", 16)
    p.drawString(200, y, "SALES REPORT")
    y -= 40

    p.setFont("Helvetica", 10)

    for s in sales:
        line = f"{s.id} | {s.product_name} | Qty: {s.quantity} | ₹{s.total_price}"
        p.drawString(50, y, line)
        y -= 20

        if y < 50:
            p.showPage()
            y = 800

    p.save()

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="sales_report.pdf",
        mimetype="application/pdf"
    )
@employee_bp.route("/create_order", methods=["POST"])
@login_required
def create_order():
    data = request.get_json()

    product_id = data.get("product_id")
    supplier_id = data.get("supplier_id")
    quantity = int(data.get("quantity"))

    product = Product.query.get(product_id)

    if not product:
        return jsonify({"error": "Product not found"})

    # 🔥 STOCK INCREASE
    product.stock += quantity

    order = Purchase(
        product_id=product_id,
        supplier_id=supplier_id,
        quantity=quantity
    )

    db.session.add(order)
    db.session.commit()

    return jsonify({"message": "Order placed & stock updated"})

@employee_bp.route("/get_orders", methods=["GET"])
@login_required
def get_orders():
    orders = Purchase.query.all()

    data = []

    for o in orders:
        data.append({
            "id": o.id,
            "product_id": o.product_id,
            "supplier_id": o.supplier_id,
            "quantity": o.quantity,
            "date": o.date.strftime("%Y-%m-%d")
        })

    return jsonify(data)

@employee_bp.route("/orders_page")
@login_required
def orders_page():
    return render_template("orders.html")