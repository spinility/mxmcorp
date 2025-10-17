from collections import OrderedDict
import time
from typing import Any, Optional


class ContextCache:
    """A simple in-process LRU TTL cache for reducing token usage by reusing results.

    - max_size: maximum number of entries to keep
    - default_ttl: default time-to-live for entries in seconds
    """

    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._store: "OrderedDict[str, tuple[Any, Optional[float]]]" = OrderedDict()

    def _is_expired(self, expiry: Optional[float]) -> bool:
        if expiry is None:
            return False
        return time.time() > expiry

    def put(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Store a value with an optional TTL (seconds)."""
        if ttl is None:
            ttl = self.default_ttl
        expiry = time.time() + ttl if ttl is not None else None
        if key in self._store:
            del self._store[key]
        self._store[key] = (value, expiry)
        self._prune()

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a value if present and not expired; otherwise return default."""
        if key not in self._store:
            return default
        value, expiry = self._store.pop(key)
        if self._is_expired(expiry):
            # expired, drop and return default
            return default
        # refresh position (most recently used)
        self._store[key] = (value, expiry)
        return value

    def exists(self, key: str) -> bool:
        if self.get(key, None) is None:
            return False
        return True

    def _prune(self) -> None:
        while len(self._store) > self.max_size:
            self._store.popitem(last=False)


def hash_query(query: str) -> str:
    """Utility to hash a string into a stable key."""
    import hashlib
    return hashlib.sha256(query.encode("utf-8")).hexdigest()


# Example usage (optional, for local testing only):
# cache = ContextCache(max_size=100, default_ttl=300)
# key = hash_query("get user settings")
# if cache.exists(key):
#     result = cache.get(key)
# else:
#     result = compute_result_somehow()
#     cache.put(key, result, ttl=60)
