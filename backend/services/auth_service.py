import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from models.user import User

def generate_jwt_token(user: User) -> str:
    """
    Generate a signed JWT token valid for 7 days.
    """
    payload = {
        "sub": user.id,
        "email": user.email,
        "role": user.role,
        "full_name": user.full_name,
        "exp": datetime.utcnow() + current_app.config["JWT_ACCESS_TOKEN_EXPIRES"],
        "iat": datetime.utcnow()
    }
    secret = current_app.config["JWT_SECRET_KEY"]
    token = jwt.encode(payload, secret, algorithm="HS256")
    return token

def decode_jwt_token(token: str) -> dict:
    """
    Decode and validate a JWT token.
    """
    secret = current_app.config["JWT_SECRET_KEY"]
    return jwt.decode(token, secret, algorithms=["HS256"])

def token_required(f):
    """
    Decorator to protect routes requiring authentication.
    Passes current_user to the decorated function.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Authorization header is missing"}), 401

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return jsonify({"error": "Authorization header must be Bearer <token>"}), 401

        token = parts[1]
        try:
            payload = decode_jwt_token(token)
            user_id = payload.get("sub")
            user = User.query.get(user_id)
            if not user or not user.is_active:
                return jsonify({"error": "User not found or inactive"}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired, please log in again"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        except Exception as e:
            return jsonify({"error": f"Authentication failed: {str(e)}"}), 401

        return f(current_user=user, *args, **kwargs)
    return decorated

def admin_required(f):
    """
    Decorator to enforce Role-Based Access Control (RBAC):
    Ensures that only users with role='admin' can access the route.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # We invoke token_required first
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Authorization header is missing"}), 401

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return jsonify({"error": "Authorization header must be Bearer <token>"}), 401

        token = parts[1]
        try:
            payload = decode_jwt_token(token)
            user_id = payload.get("sub")
            user = User.query.get(user_id)
            if not user or not user.is_active:
                return jsonify({"error": "User not found or inactive"}), 401
            if user.role != "admin":
                return jsonify({"error": "Admin privileges required for this action"}), 403
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        except Exception as e:
            return jsonify({"error": f"Authorization error: {str(e)}"}), 401

        return f(current_user=user, *args, **kwargs)
    return decorated
