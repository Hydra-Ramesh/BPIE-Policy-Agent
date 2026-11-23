import os
from datetime import timedelta
from dotenv import load_dotenv

# Load .env from current directory or parent directory
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "bpie-policy-agent-secret-key-super-secure-2026")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)

    # Neon PostgreSQL Database URL
    # Neon provides URLs starting with postgresql:// or postgres://
    raw_db_url = os.getenv("DATABASE_URL", "sqlite:///bpie_policy.db")
    if raw_db_url.startswith("postgres://"):
        raw_db_url = raw_db_url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif raw_db_url.startswith("postgresql://") and not raw_db_url.startswith("postgresql+"):
        raw_db_url = raw_db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    
    # Clean query parameters that may not be supported by libpq/psycopg2
    raw_db_url = raw_db_url.replace("&channel_binding=require", "").replace("?channel_binding=require&", "?").replace("?channel_binding=require", "")
    
    SQLALCHEMY_DATABASE_URI = raw_db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    # Groq API for LLM and Whisper STT
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

    # Qdrant Vector Database
    # If QDRANT_URL is not set, defaults to local disk vector storage
    QDRANT_URL = os.getenv("QDRANT_URL", "")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
    QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "bpie_college_policies")
    QDRANT_LOCAL_PATH = os.path.join(os.path.dirname(__file__), "qdrant_storage")

    # Embedding & Reranker Settings
    # Free FastEmbed / HuggingFace model names
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
    RERANKER_MODEL = os.getenv("RERANKER_MODEL", "ms-marco-TinyBERT-L-2-v2")

    # College Security & RBAC Configuration
    ALLOWED_EMAIL_DOMAIN = os.getenv("ALLOWED_EMAIL_DOMAIN", "@bpie.ac.in")
    ADMIN_EMAILS = [
        email.strip().lower()
        for email in os.getenv("ADMIN_EMAILS", "admin@bpie.ac.in,principal@bpie.ac.in").split(",")
        if email.strip()
    ]

    # File uploads
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
    MAX_CONTENT_LENGTH = 32 * 1024 * 1024  # 32 MB max per PDF
