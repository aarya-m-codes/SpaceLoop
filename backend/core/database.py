import logging
import sqlite3
from typing import Any
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Engine, event, text

logger = logging.getLogger("spaceloop.database")

# Initialize Flask-SQLAlchemy extension
db = SQLAlchemy()


@event.listens_for(Engine, "connect")
def configure_sqlite_connection(dbapi_connection: Any, connection_record: Any) -> None:
    """Enforce production-grade SQLite configuration via PRAGMAs on new connections.
    
    Mandated settings:
    - journal_mode = WAL (Write-Ahead Logging for high concurrency)
    - synchronous = NORMAL (Faster commits with safe crash-recovery in WAL mode)
    - busy_timeout = 5000 (Wait 5000ms on table locks before throwing operational error)
    - foreign_keys = ON (Enforce foreign key constraints)
    - temp_store = MEMORY (In-memory storage for temp tables & indices)
    - mmap_size = 268435456 (256MB memory-mapped I/O)
    """
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA journal_mode = WAL")
            cursor.execute("PRAGMA synchronous = NORMAL")
            cursor.execute("PRAGMA busy_timeout = 5000")
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.execute("PRAGMA temp_store = MEMORY")
            cursor.execute("PRAGMA mmap_size = 268435456")
        finally:
            cursor.close()
        logger.debug("Configured SQLite connection with SpaceLoop performance pragmas.")


def init_db(app: Flask) -> None:
    """Initialize database schemas within the application context."""
    with app.app_context():
        # Import models to ensure all metadata is registered with SQLAlchemy
        import models  # noqa: F401
        db.create_all()

        # Automatic schema migration for existing SQLite persistent databases
        try:
            with db.engine.connect() as conn:
                if db.engine.dialect.name == "sqlite":
                    cols = [row[1] for row in conn.execute(text("PRAGMA table_info(users)")).fetchall()]
                    if cols and "mfa_pending_secret" not in cols:
                        conn.execute(text("ALTER TABLE users ADD COLUMN mfa_pending_secret VARCHAR(255)"))
                        conn.commit()
        except Exception as exc:
            logger.debug(f"SQLite schema migration notice: {exc}")

        logger.info("Database schemas initialized successfully.")


def check_database_health() -> dict[str, Any]:
    """Execute a lightweight diagnostic query to verify database connectivity and dialect."""
    try:
        with db.engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            dialect_name = db.engine.dialect.name
            
            extra_info = {}
            if dialect_name == "sqlite":
                journal_mode = conn.execute(text("PRAGMA journal_mode")).scalar()
                foreign_keys = conn.execute(text("PRAGMA foreign_keys")).scalar()
                extra_info["sqlite_journal_mode"] = journal_mode
                extra_info["sqlite_foreign_keys"] = bool(foreign_keys)

            return {
                "status": "connected" if result == 1 else "unhealthy",
                "dialect": dialect_name,
                **extra_info
            }
    except Exception as exc:
        logger.error(f"Database health check failed: {exc}", exc_info=True)
        return {
            "status": "disconnected",
            "error": str(exc),
        }
