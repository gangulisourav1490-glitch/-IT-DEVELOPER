from flask import Blueprint, request, jsonify, session
from backend.models.user import User
from werkzeug.security import check_password_hash

auth_bp = Blueprint("auth_bp", __name__, url_prefix="/api/auth")


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data received"}), 400

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    user = User.query.filter_by(email=email).first()

    # 🔍 DEBUG (optional — baad me hata dena)
    print("USER:", user)
    print("PASSWORD FROM DB:", user.password if user else "NO USER")
    print("ROLE:", getattr(user, "role", "NO ROLE"))

    if not user or not check_password_hash(user.password, password):
        return jsonify({"error": "Invalid credentials"}), 401

    session["user_id"] = user.id
    session["user_name"] = user.name
    session["role"] = user.role  

    return jsonify({
        "message": "Login successful",
        "user": {
            "id": user.id,
            "name": user.name,
            "role": user.role
        }
    })


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"})

def is_admin():
    return session.get("role") == "admin"