"""SpaceLoop Backend Configuration Module (delegates to backend.app.config.settings).

Guarantees a SINGLE authoritative source of configuration and eliminates
divergent database locations (e.g., backend/instance vs instance).
"""
from backend.app.config.settings import (
    BASE_DIR,
    CONFIG_MAP,
    INSTANCE_DIR,
    BaseConfig,
    DevelopmentConfig,
    ProductionConfig,
    TestingConfig,
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
    "CONFIG_MAP",
    "get_config",
    "normalize_database_url",
]
