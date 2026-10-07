import threading
import time
from abc import ABC, abstractmethod
from typing import Any


class CacheInterface(ABC):
    """Abstract interface defining the cache contract."""

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        pass

    @abstractmethod
    def clear(self) -> None:
        pass

    @abstractmethod
    def has(self, key: str) -> bool:
        pass


class InMemoryCache(CacheInterface):
    """Thread-safe in-memory cache with TTL expiration support."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[Any, float | None]] = {}
        self._lock = threading.Lock()

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return default
            val, expiry = entry
            if expiry is not None and time.time() > expiry:
                del self._store[key]
                return default
            return val

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        expiry = (time.time() + ttl) if ttl is not None and ttl > 0 else None
        with self._lock:
            self._store[key] = (value, expiry)

    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._store:
                del self._store[key]
                return True
            return False

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    def has(self, key: str) -> bool:
        return self.get(key) is not None


# Global cache instance for the application
cache: CacheInterface = InMemoryCache()
