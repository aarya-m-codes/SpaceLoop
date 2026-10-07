"""SpaceLoop Persistence Session & Database Management."""
from backend.core.database import (
    check_database_health,
    configure_sqlite_connection,
    db,
    init_db,
)


def get_session():
    """Retrieve current scoped SQLAlchemy session."""
    return db.session


__all__ = [
    "db",
    "init_db",
    "check_database_health",
    "configure_sqlite_connection",
    "get_session",
]
