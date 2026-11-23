from flask import Blueprint, request, jsonify, current_app
from extensions import db
from models.user import User
from services.auth_service import generate_jwt_token, token_required
from utils.validators import is_valid_bpie_email

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()
    full_name = data.get("full_name", "").strip()

    if not email or not password or not full_name:
        return jsonify({"error": "Full name, email, and password are required"}), 400

    # Strict institute domain validation (@bpie.ac.in)
    allowed_domain = current_app.config.get("ALLOWED_EMAIL_DOMAIN", "@bpie.ac.in")
    if not is_valid_bpie_email(email, allowed_domain):
        return jsonify({
            "error": f"Invalid email domain. Only institute email addresses ending with '{allowed_domain}' are permitted."
        }), 400

    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters long"}), 400

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"error": "An account with this institute email already exists"}), 409

    # Determine role based on ADMIN_EMAILS or explicit setup
    admin_emails = current_app.config.get("ADMIN_EMAILS", [])
    role = "admin" if email in admin_emails else "student"

    # First user registered can also automatically be made admin if desired
    if User.query.count() == 0 and role != "admin":
        role = "admin"

    new_user = User(
        email=email,
        full_name=full_name,
        role=role
    )
    new_user.set_password(password)

    db.session.add(new_user)
    db.session.commit()

    token = generate_jwt_token(new_user)

    return jsonify({
        "message": "User registered successfully",
        "token": token,
        "user": new_user.to_dict()
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401

    if not user.is_active:
        return jsonify({"error": "Account is disabled. Please contact administrator."}), 403

    token = generate_jwt_token(user)

    return jsonify({
        "message": "Login successful",
        "token": token,
        "user": user.to_dict()
    }), 200


@auth_bp.route("/me", methods=["GET"])
@token_required
def get_current_user_profile(current_user: User):
    return jsonify({
        "user": current_user.to_dict()
    }), 200
