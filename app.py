from flask import Flask, render_template, redirect, session, request, jsonify
from backend.models import db
from backend.models import *
from backend.routes import auth_bp, employee_bp
from werkzeug.security import generate_password_hash
from backend.models.user import User

app = Flask(
    __name__,
    template_folder="frontend/templates",
    static_folder="frontend/static"
)

# ================= CONFIG =================
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ims.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "supersecretkey"

# Session config (IMPORTANT: before run)
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = False

db.init_app(app)

# ================= BLUEPRINTS =================
app.register_blueprint(auth_bp)
app.register_blueprint(employee_bp)

# ================= ROUTES =================

# 🔥 HOME
@app.route("/")
def home():
    return redirect("/login")


# 🔥 LOGIN PAGE
@app.route("/login")
def login_page():
    return render_template("login.html")


# 🔥 DASHBOARD
@app.route("/dashboard")
def dashboard_page():
    if "user_id" not in session:
        return redirect("/login")

    return render_template("dashboard.html")


# 🔥 CREATE USER / ADMIN (FINAL FIX)
@app.route("/create-user", methods=["POST"])
def create_user():

    # ✅ Proper indentation + data fetch
    name = request.form.get("name")
    email = request.form.get("email")
    password = request.form.get("password")
    role = request.form.get("role")

    # 🔒 Validation
    if not name or not email or not password or not role:
        return jsonify({"message": "All fields are required"}), 400

    # 🔥 Create user
    user = User(
        name=name,
        email=email,
        password=generate_password_hash(password),
        role=role
    )

    db.session.add(user)
    db.session.commit()

    # ✅ Dynamic message (fix your bug)
    return jsonify({
        "message": f"{role.capitalize()} created successfully"
    }), 200


# ================= RUN =================
if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)