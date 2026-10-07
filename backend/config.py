import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"


def normalize_database_url(url: str) -> str:
    """Normalize database URL for SQLAlchemy 2.0 compatibility.
    
    Fixes legacy postgres:// prefixes from providers like Heroku/Render to postgresql://.
    """
    if not url:
        return url
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


class BaseConfig:
    """Base configuration shared across all environments."""
    SECRET_KEY = os.getenv("SECRET_KEY", "spaceloop-insecure-dev-key-change-in-production")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "spaceloop-jwt-dev-key-change-in-production")
    JWT_ACCESS_TOKEN_EXPIRES_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", "60"))
    JWT_REFRESH_TOKEN_EXPIRES_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES_DAYS", "30"))

    # SQLAlchemy base settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = False

    # Security & limits
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", str(16 * 1024 * 1024)))  # 16 MB max payload
    CORS_ORIGINS = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "*").split(",") if origin.strip()]

    # Reverse proxy support
    ENABLE_PROXY_FIX = os.getenv("ENABLE_PROXY_FIX", "false").lower() in ("true", "1", "yes")
    NUM_PROXIES = int(os.getenv("NUM_PROXIES", "1"))

    # SpaceLoop domain constants
    GEOFENCE_RADIUS_METERS = float(os.getenv("GEOFENCE_RADIUS_METERS", "50.0"))
    ESCROW_HOLD_HOURS_AFTER_CHECKIN = int(os.getenv("ESCROW_HOLD_HOURS_AFTER_CHECKIN", "24"))
    PLATFORM_FEE_PERCENTAGE = float(os.getenv("PLATFORM_FEE_PERCENTAGE", "10.0"))
    GST_PERCENTAGE = float(os.getenv("GST_PERCENTAGE", "18.0"))

    # AI / LLM Configuration
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

    # Email Provider Configuration (resend, brevo, smtp, memory)
    EMAIL_PROVIDER = os.getenv("EMAIL_PROVIDER", "memory").lower()
    RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
    BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")
    SMTP_HOST = os.getenv("SMTP_HOST", "localhost")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    EMAIL_FROM_ADDRESS = os.getenv("EMAIL_FROM_ADDRESS", "no-reply@spaceloop.in")
    EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME", "SpaceLoop Marketplace")

    # Rate Limiting Storage
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")


class DevelopmentConfig(BaseConfig):
    """Development environment configuration using optimized SQLite."""
    DEBUG = True
    TESTING = False

    raw_db_url = os.getenv("DATABASE_URL")
    if not raw_db_url:
        INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{INSTANCE_DIR / 'spaceloop_dev.db'}"
    else:
        SQLALCHEMY_DATABASE_URI = normalize_database_url(raw_db_url)

    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {
            "timeout": 15,
            "check_same_thread": False,
        }
    }


class TestingConfig(BaseConfig):
    """Testing environment configuration with an isolated test database."""
    DEBUG = False
    TESTING = True
    SECRET_KEY = "test-secret-key-not-for-production"
    JWT_SECRET_KEY = "test-jwt-key-not-for-production"

    raw_db_url = os.getenv("TEST_DATABASE_URL")
    if not raw_db_url:
        INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{INSTANCE_DIR / 'spaceloop_test.db'}"
    else:
        SQLALCHEMY_DATABASE_URI = normalize_database_url(raw_db_url)

    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {
            "timeout": 15,
            "check_same_thread": False,
        }
    }


class ProductionConfig(BaseConfig):
    """Production environment configuration with PostgreSQL pooling."""
    DEBUG = False
    TESTING = False

    raw_db_url = os.getenv("DATABASE_URL")
    if not raw_db_url:
        # Default fallback for production must be postgresql
        SQLALCHEMY_DATABASE_URI = "postgresql://spaceloop:spaceloop@localhost:5432/spaceloop_prod"
    else:
        SQLALCHEMY_DATABASE_URI = normalize_database_url(raw_db_url)

    # Production-ready PostgreSQL connection pooling
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),
        "pool_pre_ping": True,
        "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "1800")),
        "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),
    }


CONFIG_MAP = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}


def get_config(env_name: str | None = None) -> type[BaseConfig]:
    """Retrieve the configuration class matching the requested environment."""
    if not env_name:
        env_name = os.getenv("FLASK_ENV", os.getenv("ENV", "development")).lower()
    return CONFIG_MAP.get(env_name, DevelopmentConfig)
