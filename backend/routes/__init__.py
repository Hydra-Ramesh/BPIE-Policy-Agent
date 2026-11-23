from routes.auth_routes import auth_bp
from routes.chat_routes import chat_bp
from routes.admin_routes import admin_bp
from routes.voice_routes import voice_bp

__all__ = ["auth_bp", "chat_bp", "admin_bp", "voice_bp"]
