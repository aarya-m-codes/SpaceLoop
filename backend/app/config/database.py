"""SpaceLoop Database Configuration (delegating to authoritative settings).

Guarantees a SINGLE authoritative database connection configuration
and prevents relative-path database split-brain.
"""
import os
from backend.app.config.settings import DevelopmentConfig, normalize_database_url

DATABASE_URL = normalize_database_url(os.getenv("DATABASE_URL")) or DevelopmentConfig.SQLALCHEMY_DATABASE_URI
SQLALCHEMY_DATABASE_URI = DATABASE_URL
SQLALCHEMY_TRACK_MODIFICATIONS = False

__all__ = [
    "DATABASE_URL",
    "SQLALCHEMY_DATABASE_URI",
    "SQLALCHEMY_TRACK_MODIFICATIONS",
]
