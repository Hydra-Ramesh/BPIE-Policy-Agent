import os
from flask import Flask, jsonify
from config import Config
from extensions import db, cors
from routes import auth_bp, chat_bp, admin_bp, voice_bp
from services.rag_service import RAGService
from services.voice_service import VoiceService

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})

    # Ensure uploads directory exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Initialize RAG Service (Qdrant + FastEmbed + FlashRank + Groq)
    try:
        rag_service = RAGService(
            qdrant_url=app.config.get("QDRANT_URL"),
            qdrant_api_key=app.config.get("QDRANT_API_KEY"),
            collection_name=app.config.get("QDRANT_COLLECTION"),
            local_path=app.config.get("QDRANT_LOCAL_PATH"),
            embedding_model_name=app.config.get("EMBEDDING_MODEL"),
            reranker_model_name=app.config.get("RERANKER_MODEL"),
            groq_api_key=app.config.get("GROQ_API_KEY"),
            groq_model=app.config.get("GROQ_MODEL")
        )
        app.config["RAG_SERVICE"] = rag_service
    except Exception as e:
        print(f"[create_app] Error initializing RAG Service: {e}")
        app.config["RAG_SERVICE"] = None

    # Initialize Voice Service
    try:
        voice_service = VoiceService(groq_api_key=app.config.get("GROQ_API_KEY"))
        app.config["VOICE_SERVICE"] = voice_service
    except Exception as e:
        print(f"[create_app] Error initializing Voice Service: {e}")
        app.config["VOICE_SERVICE"] = None

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(voice_bp)

    @app.route("/", methods=["GET"])
    def index():
        return jsonify({
            "service": "BPIE AI Policy Agent API",
            "status": "healthy",
            "version": "1.0.0",
            "endpoints": {
                "auth": "/api/auth",
                "chat": "/api/chat",
                "admin": "/api/admin",
                "voice": "/api/voice"
            }
        }), 200

    @app.route("/api/health", methods=["GET"])
    def health_check():
        return jsonify({
            "status": "ok",
            "database": "connected" if db.engine else "uninitialized",
            "rag_service": "ready" if app.config.get("RAG_SERVICE") else "disabled"
        }), 200

    # Auto-create tables in Neon Postgres or SQLite
    with app.app_context():
        try:
            db.create_all()
            print("[create_app] Database tables successfully verified/created.")
        except Exception as e:
            print(f"[create_app] Database connection/init warning: {e}")

    @app.errorhandler(Exception)
    def handle_exception(e):
        code = getattr(e, "code", 500)
        return jsonify({"error": str(e)}), code

    return app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
