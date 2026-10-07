"""SpaceLoop Root Configuration Module (delegates to backend.app.config.settings)."""
from backend.app.config.settings import (
    BASE_DIR,
    INSTANCE_DIR,
    BaseConfig,
    DevelopmentConfig,
    TestingConfig,
    ProductionConfig,
    get_config,
    normalize_database_url,
)

__all__ = [
    "BASE_DIR",
    "INSTANCE_DIR",
    "BaseConfig",
    "DevelopmentConfig",
    "TestingConfig",
    "ProductionConfig",
    "get_config",
    "normalize_database_url",
]
