"""SpaceLoop application package."""
from typing import Any


def create_app(*args: Any, **kwargs: Any) -> Any:
    """Lazy factory to prevent circular imports when importing backend.app submodules."""
    from backend.app.bootstrap.application import create_app as _create_app
    return _create_app(*args, **kwargs)


__all__ = ["create_app"]

